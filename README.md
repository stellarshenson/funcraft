# funcraft

Hobby animation projects: looping 19:6 banner GIFs rendered in Blender with Cycles on the GPU. Each scene project is a folder with the same internal structure.

## Projects

| Project | Contents | Output |
|---|---|---|
| `mech-design/` | BattleMech banners, from hand-drawn 2D silhouettes to rigged high-poly meshes | 5 GIFs |
| `w40k-mechanicum/` | an Adeptus Mechanicus cathedral, and ten generated scenes with rigged priests | 13 GIFs |

Each project has its own `README.md` (what it is and how to run it), `DESIGN.md` (how it is built) and `Makefile`.

## Structure

```
funcraft/
├─ README.md
├─ .claude/              skills (design-blender, design-gif, design-w40k) and the journal
├─ mech-design/
│  ├─ README.md  DESIGN.md  Makefile
│  └─ src/  in/  resources/  wip/  out/
└─ w40k-mechanicum/
   ├─ README.md  DESIGN.md  Makefile
   └─ src/  in/  resources/  references/  wip/  out/
```

Every scene project uses these folders.

| Folder | Holds | In git |
|---|---|---|
| `src/` | the scripts that generate, build, render and assemble | yes |
| `in/` | inputs the scripts load: source meshes in `in/models/`, the files as received in `in/models/originals/` | no |
| `resources/` | material the scenes use: textures and logos in `resources/assets/` | no |
| `references/` | reference material: target images, links, papers | text files only |
| `wip/` | work in progress: drafts, plates and depth, rendered frames, previews, logs, saved Blender scenes | no |
| `out/` | finished GIFs, numbered in the order they were made | no |

Work moves in one direction: `in/` and `references/` feed the scripts in `src/`, the scripts write to `wip/`, and a finished animation is assembled into `out/`. A generated texture starts as a draft in `wip/gen/`; the chosen draft becomes a file in `resources/assets/`.

## Git

Git tracks source and documents only: `src/`, the Makefiles, the Markdown documents, `.claude/`, and text files in `references/`. Inputs, resources, work in progress and outputs stay on the workstation, because together they hold several gigabytes of meshes, images and frames.
