"""Compare two PostgreSQL databases table by table (row count and content hash) and their sequences.

    python compare_postgres_databases.py postgresql://.../source postgresql://.../restored
"""
import sys, hashlib, psycopg
def snapshot(url):
    out = {}
    with psycopg.connect(url) as c:
        tables = [r[0] for r in c.execute("select table_name from information_schema.tables where table_schema='public' order by 1")]
        for t in tables:
            n = c.execute(f'select count(*) from "{t}"').fetchone()[0]
            h = c.execute(f'select md5(coalesce(string_agg(md5(x::text), \'\' order by md5(x::text)), \'\')) from "{t}" x').fetchone()[0]
            out[t] = (n, h)
        seqs = c.execute("select sequencename, last_value from pg_sequences where schemaname='public' order by 1").fetchall()
    return out, seqs
a, sa = snapshot(sys.argv[1]); b, sb = snapshot(sys.argv[2])
diff = [t for t in sorted(set(a) | set(b)) if a.get(t) != b.get(t)]
print(f"tables: source={len(a)} restored={len(b)}; rows: source={sum(v[0] for v in a.values())} restored={sum(v[0] for v in b.values())}")
print(f"tables whose row count or content hash differ: {diff or 'none'}; sequences identical: {sa == sb} ({len(sa)} sequences)")
sys.exit(1 if diff or sa != sb else 0)
