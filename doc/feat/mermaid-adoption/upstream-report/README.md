# Report rumdl blockquoted fence extraction

Pinned rumdl 0.2.78 forwards leading blockquote markers to a code-block stdin
tool. For a quoted Mermaid fence, expected raw source is
`graph LR\n  X --> Y\n`; observed source is `> graph LR\n>   X --> Y\n`.
This can reject otherwise valid Mermaid. This tiny nonblocking Work owns only
an upstream issue report or identification of an existing matching issue;
[checker implementation](../checker/README.md) can proceed independently.

Minimal Markdown input for the stdin recorder:

````markdown
> ```mermaid
> graph LR
>   X --> Y
> ```
````

- **AC-1 TODO** Given a fresh upstream duplicate search, the matching issue URL
  is recorded, or a minimal report is submitted to rumdl with pinned version
  0.2.78, a quoted fence/stdin recorder reproduction, and expected raw source
  versus actual leading `>` markers.

  Validation: search current upstream issues before submission; inspect the
  matching issue or submit the minimal reproduction and retain its issue URL
  in execution evidence for independent review. Report execution is authorized;
  this plan does not submit an issue. No upstream fix, local workaround, new
  repository tool/test, cache investigation or separate report artifact is
  required. Keep any disposable reproduction outside the checkout.
