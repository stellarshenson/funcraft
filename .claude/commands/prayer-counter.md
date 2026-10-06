Print the report of the prayer counter of the sermon page.

Run this command:

```bash
python3 "$(git rev-parse --show-toplevel)/w40k-mechanicum/src/counter.py"
```

Print its output to the user exactly as it is, as Markdown: the summary line and the two tables. Add nothing before it and nothing after it.

- The script only reads: one `GET /api/report`. Never send a `POST` to the counter and never call `/api/reset`
- If the script fails, say that the prayer counter did not answer and give the last line of the error
