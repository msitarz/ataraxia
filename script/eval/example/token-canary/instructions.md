# Instructions

For this task, permit exactly one read operation: use an available
file-reading tool or a narrow read-only command such as `cat canary.txt` to
read `canary.txt` in the current working directory. Do not list directories,
read other files, run unrelated commands, access the network, write files, or
perform any other operation. Return exactly the requested JSON object only if
the tool result contains the file contents. Never guess or fabricate the
token, or ask for it to be included in context. If the required read operation
is unavailable or the file cannot be read, return `{"error":"unavailable"}`.
