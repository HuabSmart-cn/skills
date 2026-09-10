const CATALOG_URL = 'https://static.d.gtimg.com/templates/operation.json';
const REQUEST_TIMEOUT_MS = 15_000;

const cacheBust = () => `${Date.now()}${Math.random().toString(36).slice(2, 10)}`;
const isRecord = value => !!value && typeof value === 'object' && !Array.isArray(value);

async function main() {
    const response = await fetch(`${CATALOG_URL}?t=${cacheBust()}`, {
        redirect: 'error',
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) {
        throw new Error(`Failed to fetch operation styles: HTTP ${response.status}`);
    }

    const catalog = await response.json();
    if (!Array.isArray(catalog)) {
        throw new Error('Unexpected operation catalog shape: expected an array');
    }

    const styles = catalog.flatMap(group => {
        if (!isRecord(group) || group.is_display === false || !Array.isArray(group.children)) {
            return [];
        }
        return group.children.flatMap(child => (
            isRecord(child)
            && typeof child.id === 'string'
            && child.id.trim()
            && typeof child.style === 'string'
            && child.style.trim()
                ? [{ id: child.id.trim(), style: child.style.trim() }]
                : []
        ));
    });
    process.stdout.write(`${JSON.stringify(styles)}\n`);
}

main().catch((error) => {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
});
