import os
import re
import pathlib
import datetime
from collections import Counter

MIN_LEN = 50


def extract_section(body: str, header: str) -> str:
    pattern = re.compile(rf"###\s*{re.escape(header)}\s*\n(.*?)(?=\n###|\Z)", re.S | re.I)
    m = pattern.search(body)
    return m.group(1).strip() if m else ""


def is_gibberish(text: str) -> bool:
    t = text.strip()
    if len(t) < MIN_LEN:
        return True

    letters = re.findall(r"[A-Za-zА-Яа-яЁё]", t)
    if len(letters) < len(t) * 0.5:
        return True

    vowels = re.findall(r"[AEIOUaeiouАЕЁИОУЫЭЮЯаеёиоуыэюя]", t)
    if len(vowels) < max(1, len(letters) * 0.15):
        return True

    longest_run = 1
    run = 1
    for i in range(1, len(t)):
        if t[i] == t[i - 1]:
            run += 1
            longest_run = max(longest_run, run)
        else:
            run = 1
    if longest_run > 5:
        return True

    counts = Counter(t.lower())
    most_common_ratio = counts.most_common(1)[0][1] / len(t)
    if most_common_ratio > 0.4:
        return True

    words = [w for w in t.split() if w.strip()]
    if len(words) < 3:
        return True

    avg_word_len = sum(len(w) for w in words) / len(words)
    if avg_word_len > 20:
        return True

    return False


def main():
    body = os.environ.get("ISSUE_BODY") or ""
    issue_number = os.environ.get("ISSUE_NUMBER", "0")

    telegram = extract_section(body, "Telegram")
    q1 = extract_section(body, "Что вы хотите видеть в Mesens V3")
    q2 = extract_section(body, "Что перенести из Mesens V2")
    comment = extract_section(body, "Доп. комментарий")

    telegram_ok = bool(telegram) and telegram not in ("", "-")
    q1_ok = bool(q1) and not is_gibberish(q1)
    q2_ok = bool(q2) and not is_gibberish(q2)

    verdict = "good" if (telegram_ok and q1_ok and q2_ok) else "bad"

    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", telegram.lstrip("@")) or f"issue_{issue_number}"
    folder = "beters" if verdict == "good" else "badrequest"
    pathlib.Path(folder).mkdir(exist_ok=True)

    path = f"{folder}/{safe_name}.md"
    if os.path.exists(path):
        path = f"{folder}/{safe_name}_{issue_number}.md"

    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    content = f"""# Заявка #{issue_number}

- Дата (UTC): {timestamp}
- Telegram: {telegram or '(не указан)'}
- Вердикт: {verdict}

## Что хочет видеть в Mesens V3
{q1 or '(пусто)'}

## Что перенести из Mesens V2
{q2 or '(пусто)'}

## Доп. комментарий
{comment or '-'}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"verdict={verdict}\n")
            f.write(f"path={path}\n")

    print(f"Processed issue #{issue_number}: verdict={verdict}, path={path}")


if __name__ == "__main__":
    main()
