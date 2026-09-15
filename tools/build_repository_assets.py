"""Bundle the existing licensed visual assets and the public example fixture."""

from pathlib import Path
import shutil
import xml.etree.ElementTree as ElementTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ui/vendor"
DESTINATION = ROOT / "src/blastradius/assets"
ICONS = ("arrow-right", "check", "circle-info", "code", "copy", "diagram-project", "download", "file-code", "fingerprint", "flask", "folder-open", "key", "link", "rotate-left", "server", "shield-halved", "xmark")


def main():
    for filename in ("AtkinsonHyperlegible-Regular.ttf", "Atkinson-OFL.txt", "IBMPlexSerif-Regular.ttf", "Plex-OFL.txt", "FontAwesome-LICENSE.txt"):
        shutil.copyfile(SOURCE / filename, DESTINATION / filename)
    namespace = "http://www.w3.org/2000/svg"
    ElementTree.register_namespace("", namespace)
    sprite = ElementTree.Element(f"{{{namespace}}}svg", {"class": "icon-sprite", "aria-hidden": "true", "focusable": "false"})
    for name in ICONS:
        original = ElementTree.parse(SOURCE / "icons" / f"{name}.svg").getroot()
        symbol = ElementTree.SubElement(sprite, f"{{{namespace}}}symbol", {"id": "br-" + name, "viewBox": original.attrib["viewBox"]})
        symbol.extend(list(original))
    ElementTree.ElementTree(sprite).write(DESTINATION / "review-icons.svg", encoding="unicode")
    for directory, fixture_name in (("repository-example", "aws-oidc-path"), ("repository-shared-example", "aws-oidc-shared")):
        fixture = ROOT / "tests/fixtures/repositories" / fixture_name
        for relative in (".github/workflows/deploy.yml", "infra/identity.template.json"):
            target = DESTINATION / directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fixture / relative, target)
            assert target.read_bytes() == (fixture / relative).read_bytes()
    assert len(ElementTree.parse(DESTINATION / "review-icons.svg").getroot()) == len(ICONS)
    print(f"Bundled {len(ICONS)} existing icons, 2 licensed fonts, license files and 4 declarations across 2 examples.")


if __name__ == "__main__":
    main()