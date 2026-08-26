# Contribute a ThingLoom skill

[Chinese version](README.zh-CN.md)

A contribution should take one real device through a complete, verified path.
Generating files is not enough: the hardware must produce a valid reading and
the final consumer must receive it.

## Start from the template

From the repository root:

```sh
cp -R examples/skill-template my-sensor
mv my-sensor/SKILL.md.tmpl my-sensor/SKILL.md
mv my-sensor/README.md.tmpl my-sensor/README.md
mv my-sensor/README.zh-CN.md.tmpl my-sensor/README.zh-CN.md
mv my-sensor/agents/openai.yaml.tmpl my-sensor/agents/openai.yaml
mv my-sensor/.gitignore.tmpl my-sensor/.gitignore
```

Replace every `REPLACE_ME`, then remove any optional file or section that the
skill does not need.

## Recommended layout

```text
my-sensor/
├── SKILL.md                 required agent instructions
├── README.md                English user guide
├── README.zh-CN.md          Chinese user guide
├── .gitignore               protects local output and credentials
├── agents/
│   └── openai.yaml          optional UI metadata
├── scripts/                 optional deterministic helpers and one small test
├── assets/                  optional generated-project templates and diagrams
├── references/              optional guidance loaded only when needed
└── data/                    ignored local output; never commit credentials
```

Only `SKILL.md` is required by the skill format. Add the other directories only
when the implementation uses them.

## Submission checklist

- Use a lowercase, hyphenated skill and directory name under 64 characters.
- Make the frontmatter description say exactly what the skill does and when it applies.
- Guide one real hardware path end to end and define observable completion evidence.
- Reuse existing code and tools; install only missing dependencies.
- Keep passwords and tokens out of chat, logs, committed files, and literal command text; prefer hidden prompts or protected configuration files.
- Use authenticated encrypted transport for network credentials and telemetry.
- Add one small offline test when a script contains non-trivial logic.
- Keep generated projects and build output out of Git.
- Keep the English and Chinese user guides equivalent.
- Review the staged diff for credentials, then run the tests you added and `git diff --check` before submitting.

The [DHT22](../dht22/) and [BH1750FVI](../bh1750/) skills are complete examples.
