import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';
import {
    activate,
    deactivate,
    resolvePython,
    resolveScript,
    runCopyCat,
} from './extension';

jest.mock('child_process', () => ({ spawn: jest.fn() }));
jest.mock('fs', () => ({ existsSync: jest.fn() }));

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Create a minimal fake ChildProcess with stdout/stderr EventEmitters. */
function makeMockProc(): EventEmitter & { stdout: EventEmitter; stderr: EventEmitter } {
    const proc = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter };
    proc.stdout = new EventEmitter();
    proc.stderr = new EventEmitter();
    return proc;
}

/** Configure vscode.workspace.getConfiguration per section. */
function mockCfg(
    copycat: Record<string, unknown> = {},
    python: Record<string, unknown> = {},
) {
    (vscode.workspace.getConfiguration as jest.Mock).mockImplementation(
        (section?: string) => ({
            get: (key: string, def: unknown) => {
                const map =
                    section === 'copycat' ? copycat :
                    section === 'python'  ? python  : {};
                return key in map ? (map as Record<string, unknown>)[key] : def;
            },
        }),
    );
}

function setWorkspace(fsPath: string) {
    (vscode.workspace as { workspaceFolders: unknown }).workspaceFolders = [
        { uri: { fsPath } },
    ];
}

function clearWorkspace() {
    (vscode.workspace as { workspaceFolders: unknown }).workspaceFolders = undefined;
}

// ── resolvePython ─────────────────────────────────────────────────────────────

describe('resolvePython', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        clearWorkspace();
    });

    it('returns explicit copycat.pythonPath when configured', () => {
        mockCfg({ pythonPath: '/usr/bin/python3.11' });
        expect(resolvePython()).toBe('/usr/bin/python3.11');
    });

    it('falls back to python.defaultInterpreterPath when pythonPath is empty', () => {
        mockCfg(
            { pythonPath: '' },
            { defaultInterpreterPath: '/home/user/.venv/bin/python' },
        );
        expect(resolvePython()).toBe('/home/user/.venv/bin/python');
    });

    it('returns "python" as final default when no config is set', () => {
        mockCfg({ pythonPath: '' }, { defaultInterpreterPath: 'python' });
        expect(resolvePython()).toBe('python');
    });
});

// ── resolveScript ─────────────────────────────────────────────────────────────

describe('resolveScript', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        clearWorkspace();
        (fs.existsSync as jest.Mock).mockReturnValue(false);
    });

    it('returns explicit scriptPath when the file exists', () => {
        const scriptPath = '/custom/CopyCat.py';
        mockCfg({ scriptPath });
        (fs.existsSync as jest.Mock).mockReturnValue(true);
        expect(resolveScript()).toBe(scriptPath);
    });

    it('auto-detects CopyCat.py in the workspace root', () => {
        const wsPath = '/myproject';
        const expected = path.join(wsPath, 'CopyCat.py');
        mockCfg({ scriptPath: '' });
        setWorkspace(wsPath);
        (fs.existsSync as jest.Mock).mockImplementation((p: unknown) => p === expected);
        expect(resolveScript()).toBe(expected);
    });

    it('returns undefined when workspaceFolders is empty', () => {
        mockCfg({ scriptPath: '' });
        (vscode.workspace as { workspaceFolders: unknown }).workspaceFolders = [];
        expect(resolveScript()).toBeUndefined();
    });

    it('returns undefined when CopyCat.py is not found in the workspace', () => {
        mockCfg({ scriptPath: '' });
        setWorkspace('/other');
        (fs.existsSync as jest.Mock).mockReturnValue(false);
        expect(resolveScript()).toBeUndefined();
    });
});

// ── activate / deactivate ─────────────────────────────────────────────────────

describe('activate', () => {
    let ctx: { subscriptions: unknown[] };

    beforeEach(() => {
        jest.clearAllMocks();
        ctx = { subscriptions: [] };
        activate(ctx as unknown as vscode.ExtensionContext);
    });

    it('registers copycat.run and copycat.runRecursive commands', () => {
        const ids = (vscode.commands.registerCommand as jest.Mock).mock.calls.map(
            ([id]: [string]) => id,
        );
        expect(ids).toContain('copycat.run');
        expect(ids).toContain('copycat.runRecursive');
    });

    it('creates an output channel named "CopyCat"', () => {
        expect(vscode.window.createOutputChannel).toHaveBeenCalledWith('CopyCat');
    });

    it('creates a status bar item and shows it', () => {
        expect(vscode.window.createStatusBarItem).toHaveBeenCalled();
        const sb = (vscode.window.createStatusBarItem as jest.Mock).mock.results[0].value;
        expect(sb.show).toHaveBeenCalled();
    });

    it('pushes five disposables to context.subscriptions', () => {
        expect(ctx.subscriptions).toHaveLength(5);
    });
});

describe('deactivate', () => {
    it('runs without throwing', () => {
        expect(() => deactivate()).not.toThrow();
    });
});

// ── runCopyCat ────────────────────────────────────────────────────────────────

describe('runCopyCat', () => {
    beforeAll(() => {
        // Activate once so module-level outputChannel + statusBarItem are initialised.
        activate({ subscriptions: [] } as unknown as vscode.ExtensionContext);
    });

    beforeEach(() => {
        jest.clearAllMocks();
        (fs.existsSync as jest.Mock).mockReturnValue(true);
        setWorkspace('/workspace');
        mockCfg({
            scriptPath: '/workspace/CopyCat.py',
            outputFormat: 'txt',
            maxSizeMb: 0,
            excludePatterns: [],
            extraArgs: [],
            lang: 'de',
        });
    });

    it('shows error and does not spawn when no workspace is open', () => {
        clearWorkspace();
        runCopyCat({ recursive: false });
        expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
            expect.stringContaining('Kein Workspace'),
        );
        expect(cp.spawn).not.toHaveBeenCalled();
    });

    it('falls back to copycat CLI when CopyCat.py is not found', () => {
        (fs.existsSync as jest.Mock).mockReturnValue(false);
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        mockCfg({ scriptPath: '', outputFormat: 'txt', maxSizeMb: 0, excludePatterns: [], extraArgs: [], lang: 'de' });
        runCopyCat({ recursive: false });
        const [command, args] = (cp.spawn as jest.Mock).mock.calls[0] as [string, string[]];
        expect(command).toBe('copycat');
        expect(args).not.toContain('/workspace/CopyCat.py');
        expect(cp.spawn).toHaveBeenCalled();
    });

    it('spawns python with the standard arguments', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        runCopyCat({ recursive: false });
        const [interpreter, args, opts] = (cp.spawn as jest.Mock).mock.calls[0] as [
            string, string[], Record<string, unknown>
        ];
        expect(interpreter).toBe('python');
        expect(args).toContain('/workspace/CopyCat.py');
        expect(args).toContain('--input');
        expect(args).toContain('/workspace');
        expect(args).toContain('--format');
        expect(args).toContain('txt');
        expect(args).toContain('--quiet');
        expect(args).not.toContain('--recursive');
        expect(opts).toMatchObject({ cwd: '/workspace' });
    });

    it('adds --recursive when opts.recursive is true', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        runCopyCat({ recursive: true });
        const args = (cp.spawn as jest.Mock).mock.calls[0][1] as string[];
        expect(args).toContain('--recursive');
    });

    it('adds --max-size when maxSizeMb > 0', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        mockCfg({ scriptPath: '/workspace/CopyCat.py', outputFormat: 'txt', maxSizeMb: 10, excludePatterns: [], extraArgs: [] });
        runCopyCat({ recursive: false });
        const args = (cp.spawn as jest.Mock).mock.calls[0][1] as string[];
        expect(args).toContain('--max-size');
        expect(args).toContain('10');
    });

    it('adds --exclude patterns when configured', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        mockCfg({ scriptPath: '/workspace/CopyCat.py', outputFormat: 'txt', maxSizeMb: 0, excludePatterns: ['*.min.js', 'dist/'], extraArgs: [] });
        runCopyCat({ recursive: false });
        const args = (cp.spawn as jest.Mock).mock.calls[0][1] as string[];
        expect(args).toContain('--exclude');
        expect(args).toContain('*.min.js');
        expect(args).toContain('dist/');
    });

    it('appends extraArgs to the spawn command', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        mockCfg({ scriptPath: '/workspace/CopyCat.py', outputFormat: 'txt', maxSizeMb: 0, excludePatterns: [], extraArgs: ['--search', 'TODO'], lang: 'de' });
        runCopyCat({ recursive: false });
        const args = (cp.spawn as jest.Mock).mock.calls[0][1] as string[];
        expect(args).toContain('--search');
        expect(args).toContain('TODO');
    });

    it('adds --lang when configured', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        mockCfg({ scriptPath: '/workspace/CopyCat.py', outputFormat: 'txt', maxSizeMb: 0, excludePatterns: [], extraArgs: [], lang: 'en' });
        runCopyCat({ recursive: false });
        const args = (cp.spawn as jest.Mock).mock.calls[0][1] as string[];
        expect(args).toContain('--lang');
        expect(args).toContain('en');
    });

    it('shows success message when process exits with code 0', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        runCopyCat({ recursive: false });
        proc.emit('close', 0);
        expect(vscode.window.showInformationMessage).toHaveBeenCalledWith(
            expect.stringContaining('erfolgreich'),
            expect.any(String),
        );
    });

    it('shows error message when process exits with non-zero code', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        runCopyCat({ recursive: false });
        proc.emit('close', 2);
        expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
            expect.stringContaining('Exit-Code 2'),
        );
    });

    it('shows error message on spawn error (e.g. python not in PATH)', () => {
        const proc = makeMockProc();
        (cp.spawn as jest.Mock).mockReturnValue(proc);
        runCopyCat({ recursive: false });
        proc.emit('error', new Error('spawn python ENOENT'));
        expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
            expect.stringContaining('spawn python ENOENT'),
        );
    });
});
