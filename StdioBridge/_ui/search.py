import os


def search():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                text = open(os.path.join(root, file), 'r').read()
                if ('from StdioBridge' in text or 'import StdioBridge' in text) and 'BridgeAPI' in text:
                    return os.path.join(root, file)
