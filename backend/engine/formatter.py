"""
engine/formatter.py
-------------------
The Format Engine layer of the Backend Orchestrator.
Ensures all LLM outputs meet strict markdown and stylistic standards.
"""

import re

class FormatEngine:
    @staticmethod
    def ensure_standard_format(text: str, mode: str) -> str:
        """
        Enforces ## Title, structural headers, and cleans LLM noise based on intent.
        """
        if not text:
            return ""
            
        # 1. Expanded Noise Cleaning (Fix #6) — 25 patterns vs original 5
        noise_patterns = [
            # Opening preambles (single-model most common outputs)
            r"^(Sure|Of course|Certainly|Absolutely|Great|Alright|Okay|OK)[,!.]\s*[\n]?",
            r"^(Sure|Of course|Certainly|Absolutely|Great|Alright|Okay|OK)[,!.]?\s+(here|let me|I'll|I will|I'd).*?\n",
            r"^(I'd be happy|I'm happy|I'll help|Let me help|Let me break|Let me explain).*?\n",
            r"^(Here's what|Here is what|Here's|Here is|Below is|Below are|The following).*?:\s*\n",
            r"^(Based on|Based upon|According to my|According to the|As requested).*?\n",
            r"^(As an AI|As a language model|As an artificial|I am an AI).*?\n",
            r"^(This is a|This is an|This response|This report).*?:\s*\n",
            r"^(Note:|Please note|Important note|Disclaimer):.*?\n",
            r"^(Great question|That's a great|What a great|Excellent question).*?\n",
            # Closing filler (strip from end)
            r"\n(I hope this helps|I hope that helps)[.!]?\s*$",
            r"\n(Let me know if you (need|have|want).*?)[.!]?\s*$",
            r"\n(Feel free to ask.*?)[.!]?\s*$",
            r"\n(Is there anything else.*?)[.!?]?\s*$",
            r"\n(Would you like me to.*?)[.!?]?\s*$",
            r"\n(Please (let me know|feel free).*?)[.!?]?\s*$",
            r"\n(If you have any (further|more|other|additional).*?)[.!?]?\s*$",
        ]
        cleaned_text = text
        for pattern in noise_patterns:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        cleaned_text = cleaned_text.strip()
        
        # 2. Intent Detection
        has_code = "```" in cleaned_text
        has_list = "- " in cleaned_text or "* " in cleaned_text or re.search(r"\d+\. ", cleaned_text)
        is_short = len(cleaned_text.split()) < 30
        
        # 3. Conversational Skip for Greetings
        # Safely get first 20 chars
        prefix = cleaned_text.lower()
        if len(prefix) > 20:
            prefix = prefix[0:20]
        
        is_greeting = any(kw in prefix for kw in ["hi", "hello", "hey", "greetings", "how can i"])
        if is_greeting and is_short:
             return cleaned_text

        # 4. TECH/CODE UPGRADE
        if has_code and not cleaned_text.startswith("## tech"):
            if "### usage" not in cleaned_text.lower():
                # If it's pure code without explanation, keep it clean
                if not any(header in cleaned_text for header in ["## ", "### "]):
                    return cleaned_text
            
        # 5. ANALYSIS/RESEARCH UPGRADE
        if mode in ["research", "deep", "analyze"]:
            # Ensure Header if missing
            if not cleaned_text.startswith("## "):
                lines = cleaned_text.split('\n')
                first_line = lines[0]
                if 5 < len(first_line) < 70 and not any(c in first_line for c in ["#", "|", "*"]):
                    rest = ""
                    if len(lines) > 1:
                        # Reconstruct safely
                        rest_lines = []
                        for i in range(1, len(lines)):
                            rest_lines.append(lines[i])
                        rest = "\n".join(rest_lines)
                    cleaned_text = f"## {first_line}\n\n" + rest
                else:
                    cleaned_text = f"## Intelligence Analysis Report\n\n" + cleaned_text
            
            # Ensure Summary section exists for long reports
            if len(cleaned_text) > 800 and "### summary" not in cleaned_text.lower():
                 cleaned_text = cleaned_text.replace("## ", "## Intelligence Summary\n\n> [!NOTE]\n> This report is synthesized using local neural reasoning.\n\n## ", 1)

        # 7. 🎭 DYNAMIC EMOJI HYDRATION (High-Density Aesthetic)
        cleaned_text = FormatEngine._hydrate_emojis(cleaned_text)
        
        # 8. 🏗️ VISUAL POLISH (Layout Optimization)
        cleaned_text = FormatEngine.polish_markdown_layout(cleaned_text)
        
        return cleaned_text

    @staticmethod
    def _hydrate_emojis(text: str) -> str:
        """ADVANCED: Injects semantic, context-aware emojis — high-density, always-on."""
        if not text: return ""

        # 1. EXPANDED SEMANTIC PALETTE
        PALETTE = {
            "tech":       ["💻", "🏗️", "⚙️", "🛠️", "🔬", "🖥️", "🧩"],
            "research":   ["🔍", "🕵️", "📑", "🧭", "📊", "🗂️", "🧠"],
            "creative":   ["✍️", "🎨", "✨", "🎬", "💭", "🖌️", "🎭"],
            "alert":      ["⚠️", "🛑", "🚩", "❗", "⚡", "🔴", "🔔"],
            "growth":     ["🚀", "📈", "🏆", "✅", "🌟", "💡", "🎯"],
            "financial":  ["💎", "💰", "🏦", "📊", "📈", "💳", "🪙"],
            "legal":      ["🛡️", "⚖️", "📜", "🖊️", "🏛️", "🔏", "📋"],
            "health":     ["🏥", "🧪", "🧬", "🧘", "❤️", "🩺", "💊"],
            "data":       ["📊", "📋", "🔢", "🗄️", "📑", "🔗", "📉"],
            "learning":   ["📚", "🎓", "✏️", "🗒️", "💡", "🧑‍🏫", "📖"],
            "travel":     ["🌍", "✈️", "🗺️", "🏖️", "🧳", "🌄", "🚂"],
            "security":   ["🔐", "🛡️", "🔒", "🔑", "🚔", "🧱", "🕵️"],
            "chat":       ["💬", "🗣️", "👋", "😊", "🤝", "💡", "✨"],
        }

        # 2. KEYWORD → CATEGORY MAPPING  (much broader than before)
        KEYWORD_MAP = {
            "tech":      [r"code", r"python", r"api", r"server", r"infra", r"debug", r"patch",
                          r"deploy", r"docker", r"model", r"function", r"class", r"module",
                          r"import", r"error", r"bug", r"fix", r"install", r"package", r"npm",
                          r"javascript", r"react", r"sql", r"database", r"endpoint"],
            "research":  [r"analysis", r"study", r"verify", r"source", r"investigate", r"evidence",
                          r"report", r"research", r"data shows", r"according", r"findings",
                          r"conclusion", r"hypothesis", r"results", r"statistics"],
            "financial": [r"price", r"cost", r"roi", r"market", r"budget", r"investment",
                          r"profit", r"loss", r"revenue", r"expense", r"stock", r"crypto"],
            "growth":    [r"roadmap", r"future", r"milestone", r"success", r"launch",
                          r"upcoming", r"goal", r"target", r"achieve", r"improve", r"upgrade",
                          r"enhance", r"better", r"faster", r"optimize"],
            "alert":     [r"warning", r"danger", r"critical", r"important", r"urgent", r"note",
                          r"caution", r"error", r"fail", r"issue", r"problem", r"risk"],
            "security":  [r"security", r"auth", r"token", r"encrypt", r"protect", r"vulnerab",
                          r"attack", r"firewall", r"permission", r"sandbox"],
            "learning":  [r"learn", r"understand", r"explain", r"concept", r"tutorial",
                          r"step", r"guide", r"how to", r"lesson", r"teach", r"education"],
            "data":      [r"table", r"chart", r"graph", r"metric", r"measure", r"statistic",
                          r"dataset", r"record", r"column", r"row", r"query"],
            "health":    [r"health", r"medical", r"symptom", r"treatment", r"exercise",
                          r"wellness", r"disease", r"nutrition", r"mental"],
            "travel":    [r"travel", r"trip", r"country", r"city", r"flight", r"hotel",
                          r"location", r"destination", r"map", r"itinerary"],
            "chat":      [r"hello", r"hi ", r"hey", r"assist", r"help", r"sure", r"great",
                          r"glad", r"happy", r"welcome", r"please", r"thank"],
        }

        # 3. Determine dominant vibe from full text
        text_lower = text.lower()
        vibe = "chat"  # safe default
        best_hits = 0
        for cat, kws in KEYWORD_MAP.items():
            hits = sum(1 for kw in kws if re.search(kw, text_lower))
            if hits > best_hits:
                best_hits = hits
                vibe = cat

        primary_emoji = PALETTE[vibe][0]
        secondary_emoji = PALETTE[vibe][1] if len(PALETTE[vibe]) > 1 else primary_emoji

        # 4. Per-line injection
        lines = text.split('\n')
        hydrated = []

        for line in lines:
            lw = line.lower().strip()

            # Headers — always inject emoji if not already present
            if line.startswith("## "):
                has_emoji = any(ord(c) > 127 for c in line[3:6])
                if not has_emoji:
                    line = line.replace("## ", f"## {primary_emoji} ", 1)

            elif line.startswith("### "):
                has_emoji = any(ord(c) > 127 for c in line[4:7])
                if not has_emoji:
                    sub = "⚙️"
                    if any(w in lw for w in ["summary", "overview", "tldr"]): sub = "📝"
                    elif any(w in lw for w in ["conclusion", "result", "outcome"]): sub = "🏁"
                    elif any(w in lw for w in ["step", "how", "guide", "install"]): sub = "🗺️"
                    elif any(w in lw for w in ["data", "table", "metric", "stat"]): sub = "📊"
                    elif any(w in lw for w in ["security", "auth", "protect"]): sub = "🔐"
                    elif any(w in lw for w in ["tip", "note", "info", "hint"]): sub = "💡"
                    elif any(w in lw for w in ["warning", "caution", "error", "fail"]): sub = "⚠️"
                    line = line.replace("### ", f"### {sub} ", 1)

            elif line.startswith("#### "):
                has_emoji = any(ord(c) > 127 for c in line[5:8])
                if not has_emoji:
                    line = line.replace("#### ", f"#### 🔹 ", 1)

            # Bullet points — inject lead emoji per topic match
            elif line.strip().startswith(("- ", "* ")):
                has_emoji = any(ord(c) > 127 for c in lw[:8])
                if not has_emoji:
                    bullet_emoji = secondary_emoji
                    for cat, kws in KEYWORD_MAP.items():
                        if any(re.search(kw, lw) for kw in kws):
                            bullet_emoji = PALETTE[cat][2] if len(PALETTE[cat]) > 2 else PALETTE[cat][0]
                            break
                    # Replace just the dash/star prefix
                    stripped = line.lstrip()
                    indent = line[:len(line) - len(stripped)]
                    prefix = stripped[:2]  # "- " or "* "
                    rest = stripped[2:]
                    line = f"{indent}{prefix}{bullet_emoji} {rest}"

            # Standalone paragraph lines (>6 words, no existing emoji)
            elif len(lw.split()) > 6 and not line.startswith(("#", "|", ">")):
                has_emoji = any(ord(c) > 127 for c in line[:6])
                if not has_emoji:
                    for cat, kws in KEYWORD_MAP.items():
                        if any(re.search(kw, lw) for kw in kws):
                            line = f"{PALETTE[cat][0]} {line}"
                            break

            hydrated.append(line)

        return "\n".join(hydrated)

    @staticmethod
    def polish_markdown_layout(text: str) -> str:
        """Dynamically applies advanced visual layouts based on content structure."""
        if not text: return ""
        
        # 1. AUTO-TABLE: Detect key value pairs that should be in a table
        if "- **" in text and ":" in text and text.count("- **") > 3:
            # Simple heuristic: if we have a list of bold keys with colons, try to tabularize
            lines = text.split('\n')
            new_lines = []
            table_buffer = []
            for line in lines:
                if line.strip().startswith("- **") and ":" in line:
                    table_buffer.append(line)
                else:
                    if len(table_buffer) > 2:
                        header = "| Component | Description |\n| :--- | :--- |\n"
                        table_rows = []
                        for row in table_buffer:
                            parts = row.replace("- **", "").split(":", 1)
                            key = parts[0].replace("**", "").strip()
                            val = parts[1].strip() if len(parts) > 1 else ""
                            table_rows.append(f"| **{key}** | {val} |")
                        new_lines.append(header + "\n".join(table_rows))
                        table_buffer = []
                    elif table_buffer: # Just add back the lines if not enough for a table
                        new_lines.extend(table_buffer)
                        table_buffer = []
                    new_lines.append(line)
            text = "\n".join(new_lines)

        # 2. Checklist Upgrade: Turn steps into checklists
        text = re.sub(r"\n(\d+)\. ", r"\n\1. [ ] ", text)
        
        # 3. Callout Box: Wrap Summaries
        if "### Summary" in text or "### 📝 Executive Summary" in text:
             text = re.sub(r"(### (?:📝 )?Executive Summary\n)(.*?)(\n\n)", r"\1> [!NOTE]\n> \2\3", text, flags=re.S)

        return text

    @staticmethod
    def stream_post_process(token: str, state: dict) -> str:
        """
        Optional: Handle real-time stream cleaning if needed.
        Currently just returns token as buffering is done at completion.
        """
        return token
