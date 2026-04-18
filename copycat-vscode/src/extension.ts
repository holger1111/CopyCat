import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

let outputChannel: vscode.OutputChannel;
let statusBarItem: vscode.StatusBarItem;

// ── Aktivierung ──────────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext): void {
    outputChannel = vscode.window.createOutputChannel('CopyCat');

    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Left,
        0,
    );
    statusBarItem.command = 'copycat.run';
    statusBarItem.text = '$(file-code) CopyCat';
    statusBarItem.tooltip = 'CopyCat: Report erstellen';
    statusBarItem.show();

    context.subscriptions.push(
        vscode.commands.registerCommand('copycat.run', () =>
            runCopyCat({ recursive: false }),
        ),
        vscode.commands.registerCommand('copycat.runRecursive', () =>
            runCopyCat({ recursive: true }),
        ),
        outputChannel,
        statusBarItem,
    );
}

// ── Deaktivierung ─────────────────────────────────────────────────────────────

export function deactivate(): void {
    // Subscriptions werden automatisch durch context.subscriptions disposed.
}

// ── Hilfsfunktionen ───────────────────────────────────────────────────────────

/**
 * Ermittelt den Python-Interpreter-Pfad.
 * Priorität: copycat.pythonPath → python.defaultInterpreterPath → 'python'
 */
export function resolvePython(): string {
    const cfg = vscode.workspace.getConfiguration('copycat');
    const explicit = cfg.get<string>('pythonPath', '').trim();
    if (explicit) {
        return explicit;
    }

    // Fallback: Python-Extension-Einstellung
    const pythonCfg = vscode.workspace.getConfiguration('python');
    const interpreterPath = pythonCfg.get<string>('defaultInterpreterPath', '').trim();
    if (interpreterPath && interpreterPath !== 'python') {
        return interpreterPath;
    }

    return 'python';
}

/**
 * Ermittelt den Pfad zu CopyCat.py.
 * Priorität: copycat.scriptPath → CopyCat.py im Workspace-Stammverzeichnis
 */
export function resolveScript(): string | undefined {
    const cfg = vscode.workspace.getConfiguration('copycat');
    const explicit = cfg.get<string>('scriptPath', '').trim();
    if (explicit && fs.existsSync(explicit)) {
        return explicit;
    }

    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
        return undefined;
    }

    const candidate = path.join(folders[0].uri.fsPath, 'CopyCat.py');
    return fs.existsSync(candidate) ? candidate : undefined;
}

// ── Hauptlogik ────────────────────────────────────────────────────────────────

export interface RunOptions {
    recursive: boolean;
}

export function runCopyCat(opts: RunOptions): void {
    // Workspace prüfen
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
        vscode.window.showErrorMessage('CopyCat: Kein Workspace-Ordner geöffnet.');
        return;
    }

    // CopyCat.py ermitteln
    const script = resolveScript();
    if (!script) {
        vscode.window.showErrorMessage(
            'CopyCat: CopyCat.py nicht gefunden. '
            + 'Bitte copycat.scriptPath in den Einstellungen konfigurieren.',
            'Einstellungen öffnen',
        ).then(choice => {
            if (choice === 'Einstellungen öffnen') {
                vscode.commands.executeCommand(
                    'workbench.action.openSettings',
                    'copycat.scriptPath',
                );
            }
        });
        return;
    }

    // Argumente aufbauen
    const python = resolvePython();
    const inputDir = folders[0].uri.fsPath;
    const cfg = vscode.workspace.getConfiguration('copycat');

    const fmt = cfg.get<string>('outputFormat', 'txt');
    const maxSize = cfg.get<number>('maxSizeMb', 0);
    const excludePatterns = cfg.get<string[]>('excludePatterns', []);
    const extraArgs = cfg.get<string[]>('extraArgs', []);

    const args: string[] = [script, '--input', inputDir, '--format', fmt, '--quiet'];

    if (opts.recursive) {
        args.push('--recursive');
    }
    if (maxSize > 0) {
        args.push('--max-size', String(maxSize));
    }
    if (excludePatterns.length > 0) {
        args.push('--exclude', ...excludePatterns);
    }
    if (extraArgs.length > 0) {
        args.push(...extraArgs);
    }

    // Output Channel öffnen und Lauf starten
    outputChannel.clear();
    outputChannel.show(true);
    outputChannel.appendLine(
        `▶  CopyCat${opts.recursive ? ' (rekursiv)' : ''}  –  ${new Date().toLocaleTimeString()}`,
    );
    outputChannel.appendLine(`   ${python} ${args.join(' ')}`);
    outputChannel.appendLine('─'.repeat(60));

    statusBarItem.text = '$(sync~spin) CopyCat …';
    statusBarItem.tooltip = 'CopyCat läuft …';

    const proc = cp.spawn(python, args, { cwd: inputDir });

    proc.stdout.on('data', (data: Buffer) => outputChannel.append(data.toString()));
    proc.stderr.on('data', (data: Buffer) => outputChannel.append(data.toString()));

    proc.on('close', (code: number | null) => {
        const exitCode = code ?? -1;
        outputChannel.appendLine('─'.repeat(60));

        statusBarItem.text = '$(file-code) CopyCat';
        statusBarItem.tooltip = 'CopyCat: Report erstellen';

        if (exitCode === 0) {
            outputChannel.appendLine('✓  Abgeschlossen.');
            vscode.window
                .showInformationMessage(
                    'CopyCat: Report erfolgreich erstellt.',
                    'Ordner öffnen',
                )
                .then(choice => {
                    if (choice === 'Ordner öffnen') {
                        vscode.commands.executeCommand(
                            'revealFileInOS',
                            vscode.Uri.file(inputDir),
                        );
                    }
                });
        } else {
            outputChannel.appendLine(`✗  Fehler (Exit-Code ${exitCode}).`);
            vscode.window.showErrorMessage(`CopyCat: Fehler (Exit-Code ${exitCode}).`);
        }
    });

    proc.on('error', (err: Error) => {
        statusBarItem.text = '$(file-code) CopyCat';
        statusBarItem.tooltip = 'CopyCat: Report erstellen';
        outputChannel.appendLine(`✗  Fehler beim Starten: ${err.message}`);
        vscode.window.showErrorMessage(
            `CopyCat: Python konnte nicht gestartet werden – ${err.message}`,
        );
    });
}
