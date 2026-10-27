def where(q):
    clauses, args = ['timestamp IS NOT NULL'], []
    ids = q.get('file_ids', [])
    if not ids:
        return '0', []
    clauses.append('file_id IN ('+','.join('?' for _ in ids)+')'); args.extend(ids)
    groups = []
    for f in q.get('filters', []):
        subs = f.get('submodules')
        if subs == []: continue
        args.append(f['tag'])
        if subs is None:
            groups.append('(tag=?)'); continue
        parts = []
        names = [s for s in subs if s is not None]
        if names:
            parts.append('submodule IN ('+','.join('?' for _ in names)+')'); args.extend(names)
        if None in subs: parts.append('submodule IS NULL')
        groups.append('(tag=? AND ('+' OR '.join(parts)+'))')
    clauses.append('('+' OR '.join(groups)+')' if groups else '0')
    for key, op in [('start','>='),('end','<=')]:
        if q.get(key) is not None:
            clauses.append('timestamp'+op+'?'); args.append(q[key])
    if q.get('levels'):
        clauses.append('level IN ('+','.join('?' for _ in q['levels'])+')'); args.extend(q['levels'])
    if q.get('keyword'):
        clauses.append('instr(message,?)>0'); args.append(q['keyword'])
    return ' AND '.join(clauses), args
