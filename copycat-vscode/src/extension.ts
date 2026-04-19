import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

let outputChannel: vscode.OutputChannel;
let statusBarItem: vscode.StatusBarItem;

// ── Aktivierung ──────────────────────────────────────────────────────────────

async function checkRequirements(): Promise<boolean> {
    const python = resolvePython();
    const pythonWorks = await commandExists(python);

    if (!pythonWorks) {
        const choice = await vscode.window.showErrorMessage(
            'CopyCat: Python nicht gefunden. Installiere Python von python.org.',
            'Zur Dokumentation',
            'Abbrechen',
        );
        if (choice === 'Zur Dokumentation') {
            vscode.env.openExternal(vscode.Uri.parse('https://python.org'));
        }
        return false;
    }

    const scriptExists = resolveScript();
    const copycatCliExists = await commandExists('copycat');

    if (!scriptExists && !copycatCliExists) {
        const choice = await vscode.window.showWarningMessage(
            'CopyCat: Weder CopyCat.py noch `copycat` CLI gefunden.',
            'copycat-tool installieren',
            'Selbst installieren',
            'Abbrechen',
        );

        if (choice === 'copycat-tool installieren') {
            await installCopycatTool();
            return true;
        } else if (choice === 'Selbst installieren') {
            vscode.env.openExternal(
                vscode.Uri.parse('https://github.com/holger1111/CopyCat'),
            );
        }
        return false;
    }

    return true;
}

async function commandExists(cmd: string): Promise<boolean> {
    try {
        await new Promise((resolve, reject) => {
            const proc = cp.spawn(cmd === 'copycat' ? 'copycat' : cmd, ['--version'], {
                timeout: 5000,
                windowsHide: true,
            });
            proc.on('close', (code: number | null) => {
                resolve(code === 0);
            });
            proc.on('error', () => reject(new Error('Command not found')));
        });
        return true;
    } catch {
        return false;
    }
}

async function installCopycatTool(): Promise<void> {
    outputChannel.clear();
    outputChannel.show(true);
    outputChannel.appendLine('▶  pip install copycat-tool');
    outputChannel.appendLine('─'.repeat(60));

    const python = resolvePython();
    const proc = cp.spawn(python, ['-m', 'pip', 'install', '--upgrade', 'copycat-tool'], {
        windowsHide: true,
    });

    return new Promise((resolve, reject) => {
        proc.stdout?.on('data', (data: Buffer) => outputChannel.append(data.toString()));
        proc.stderr?.on('data', (data: Buffer) => outputChannel.append(data.toString()));
        proc.on('close', (code: number | null) => {
            outputChannel.appendLine('─'.repeat(60));
            if (code === 0) {
                outputChannel.appendLine('✓  copycat-tool erfolgreich installiert.');
                vscode.window.showInformationMessage('CopyCat: copycat-tool installiert.');
                resolve();
            } else {
                outputChannel.appendLine(`✗  Installation fehlgeschlagen (Exit-Code ${code}).`);
                vscode.window.showErrorMessage(
                    `CopyCat: Installation fehlgeschlagen. Siehe Output-Channel.`,
                );
                reject(new Error(`Installation failed with code ${code}`));
            }
        });
        proc.on('error', (err: Error) => {
            outputChannel.appendLine(`✗  Fehler: ${err.message}`);
            reject(err);
        });
    });
}

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
        vscode.commands.registerCommand('copycat.checkRequirements', () =>
            checkRequirements(),
        ),
        outputChannel,
        statusBarItem,
    );

    // Beim Start automatisch Voraussetzungen prüfen
    checkRequirements().catch(() => {
        // Fehler werden bereits dem Nutzer angezeigt
    });
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
 * Gibt undefined zurück wenn nicht gefunden (dann wird `copycat` CLI verwendet).
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

    // CopyCat.py ermitteln; falls nicht gefunden, `copycat` CLI aus PATH verwenden
    const script = resolveScript();

    // Argumente aufbauen
    const python = resolvePython();
    const inputDir = folders[0].uri.fsPath;
    const cfg = vscode.workspace.getConfiguration('copycat');

    const fmt = cfg.get<string>('outputFormat', 'txt');
    const maxSize = cfg.get<number>('maxSizeMb', 0);
    const excludePatterns = cfg.get<string[]>('excludePatterns', []);
    const extraArgs = cfg.get<string[]>('extraArgs', []);
    const lang = cfg.get<string>('lang', 'de');

    // Wenn CopyCat.py vorhanden: `python CopyCat.py …`, sonst: `copycat …`
    let command: string;
    let args: string[];
    if (script) {
        command = python;
        args = [script, '--input', inputDir, '--format', fmt, '--quiet'];
    } else {
        command = 'copycat';
        args = ['--input', inputDir, '--format', fmt, '--quiet'];
    }

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
    args.push('--lang', lang);

    // Output Channel öffnen und Lauf starten
    outputChannel.clear();
    outputChannel.show(true);
    outputChannel.appendLine(
        `▶  CopyCat${opts.recursive ? ' (rekursiv)' : ''}  –  ${new Date().toLocaleTimeString()}`,
    );
    outputChannel.appendLine(`   ${command} ${args.join(' ')}`);
    outputChannel.appendLine('─'.repeat(60));

    statusBarItem.text = '$(sync~spin) CopyCat …';
    statusBarItem.tooltip = 'CopyCat läuft …';

    const proc = cp.spawn(command, args, { cwd: inputDir });

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
