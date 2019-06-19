# Trello Report Generator

Generates a weekly report based on progress in a Trello board. Requires the user to provide the necessary keys beforehand (currently has no OAuth flow implemented).

## Example Command

```bash
python3 reportgen make \
    --access-key=YOUR_KEY \
    --access-token=YOUR_TOKEN \
    --work-board=Work \
    --completed-list=Completed \
    --next-list="This Week" \
    --blocked-list=Blocked
```
