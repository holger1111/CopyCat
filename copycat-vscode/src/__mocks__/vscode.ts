/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Manual Jest mock for the `vscode` module.
 * Loaded automatically via moduleNameMapper in package.json.
 */

export enum StatusBarAlignment {
    Left = 1,
    Right = 2,
}

export const Uri = {
    file: jest.fn((p: string) => ({ fsPath: p })),
};

export const window = {
    createOutputChannel: jest.fn().mockReturnValue({
        clear: jest.fn(),
        show: jest.fn(),
        append: jest.fn(),
        appendLine: jest.fn(),
        dispose: jest.fn(),
    }),
    createStatusBarItem: jest.fn().mockReturnValue({
        command: '' as string,
        text: '' as string,
        tooltip: '' as string,
        show: jest.fn(),
        dispose: jest.fn(),
    }),
    showErrorMessage: jest.fn().mockResolvedValue(undefined),
    showInformationMessage: jest.fn().mockResolvedValue(undefined),
};

export const workspace = {
    workspaceFolders: undefined as any,
    getConfiguration: jest.fn().mockReturnValue({
        get: jest.fn().mockReturnValue(''),
    }),
};

export const commands = {
    registerCommand: jest.fn().mockReturnValue({ dispose: jest.fn() }),
    executeCommand: jest.fn().mockResolvedValue(undefined),
};
