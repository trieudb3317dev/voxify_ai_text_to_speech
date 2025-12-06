#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script dịch file README.md sang ngôn ngữ khác
Usage: python translate_readme.py [--source README.md] [--target en] [--output README_EN.md]
"""
import argparse
import re
import sys
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
    HAS_DEEP_TRANSLATOR = True
except ImportError:
    try:
        from googletrans import Translator
        HAS_GOOGLETRANS = True
        HAS_DEEP_TRANSLATOR = False
    except ImportError:
        HAS_GOOGLETRANS = False
        HAS_DEEP_TRANSLATOR = False

# Mapping ngôn ngữ
LANG_MAP = {
    'vi': 'vi',
    'en': 'en',
    'vi-VN': 'vi',
    'en-US': 'en',
    'vietnamese': 'vi',
    'english': 'en'
}

def detect_language(text):
    """Phát hiện ngôn ngữ của text (đơn giản)"""
    # Kiểm tra một số từ tiếng Việt phổ biến
    vietnamese_words = ['của', 'và', 'với', 'cho', 'được', 'là', 'có', 'trong', 'này', 'để']
    words = text.lower().split()
    vi_count = sum(1 for word in words if word in vietnamese_words)
    
    if vi_count > len(words) * 0.1:  # Nếu > 10% từ là tiếng Việt
        return 'vi'
    return 'en'

def translate_text(text, source_lang, target_lang, translator=None):
    """Dịch text sử dụng translator"""
    if not text.strip():
        return text
    
    try:
        if HAS_DEEP_TRANSLATOR:
            if translator is None:
                translator = GoogleTranslator(source=source_lang, target=target_lang)
            return translator.translate(text)
        elif HAS_GOOGLETRANS:
            if translator is None:
                translator = Translator()
            result = translator.translate(text, src=source_lang, dest=target_lang)
            return result.text
        else:
            print("❌ Không tìm thấy thư viện dịch. Cài đặt: pip install deep-translator hoặc googletrans")
            return text
    except Exception as e:
        print(f"⚠️  Lỗi khi dịch: {e}")
        return text

def parse_markdown(content):
    """Phân tích markdown thành các phần: text, code blocks, links, etc."""
    parts = []
    i = 0
    
    # Pattern cho code blocks
    code_block_pattern = re.compile(r'```[\s\S]*?```')
    # Pattern cho inline code
    inline_code_pattern = re.compile(r'`[^`]+`')
    # Pattern cho links
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
    # Pattern cho URLs
    url_pattern = re.compile(r'https?://[^\s\)]+')
    
    while i < len(content):
        # Tìm code block
        code_match = code_block_pattern.search(content, i)
        if code_match:
            # Text trước code block
            if code_match.start() > i:
                text_before = content[i:code_match.start()]
                parts.append(('text', text_before))
            # Code block
            parts.append(('code', code_match.group()))
            i = code_match.end()
            continue
        
        # Nếu không có code block, xử lý text bình thường
        # Tìm code block tiếp theo
        next_code = code_block_pattern.search(content, i)
        next_pos = next_code.start() if next_code else len(content)
        
        text_segment = content[i:next_pos]
        parts.append(('text', text_segment))
        i = next_pos
    
    return parts

def translate_markdown(content, source_lang='auto', target_lang='en'):
    """Dịch markdown content, giữ nguyên format"""
    if source_lang == 'auto':
        source_lang = detect_language(content[:500])  # Lấy mẫu để detect
    
    # Normalize language codes
    source_lang = LANG_MAP.get(source_lang.lower(), source_lang)
    target_lang = LANG_MAP.get(target_lang.lower(), target_lang)
    
    print(f"🌐 Dịch từ {source_lang} sang {target_lang}...")
    
    # Phân tích markdown
    parts = parse_markdown(content)
    
    # Khởi tạo translator
    translator = None
    if HAS_DEEP_TRANSLATOR:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
    elif HAS_GOOGLETRANS:
        translator = Translator()
    
    translated_parts = []
    total_parts = len([p for p in parts if p[0] == 'text'])
    current_part = 0
    
    for part_type, part_content in parts:
        if part_type == 'code':
            # Giữ nguyên code blocks
            translated_parts.append(part_content)
        else:
            # Dịch text, nhưng giữ nguyên inline code và links
            text = part_content
            
            # Bảo vệ inline code
            inline_codes = {}
            code_counter = 0
            for match in re.finditer(r'`([^`]+)`', text):
                placeholder = f"__INLINE_CODE_{code_counter}__"
                inline_codes[placeholder] = match.group(0)
                text = text.replace(match.group(0), placeholder)
                code_counter += 1
            
            # Bảo vệ URLs
            urls = {}
            url_counter = 0
            for match in re.finditer(r'https?://[^\s\)]+', text):
                placeholder = f"__URL_{url_counter}__"
                urls[placeholder] = match.group(0)
                text = text.replace(match.group(0), placeholder)
                url_counter += 1
            
            # Bảo vệ links [text](url)
            links = {}
            link_counter = 0
            for match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', text):
                placeholder = f"__LINK_{link_counter}__"
                links[placeholder] = match.group(0)
                text = text.replace(match.group(0), placeholder)
                link_counter += 1
            
            # Dịch text
            if text.strip():
                current_part += 1
                print(f"📝 Đang dịch phần {current_part}/{total_parts}...", end='\r')
                translated = translate_text(text, source_lang, target_lang, translator)
            else:
                translated = text
            
            # Khôi phục inline code
            for placeholder, original in inline_codes.items():
                translated = translated.replace(placeholder, original)
            
            # Khôi phục URLs
            for placeholder, original in urls.items():
                translated = translated.replace(placeholder, original)
            
            # Khôi phục links
            for placeholder, original in links.items():
                translated = translated.replace(placeholder, original)
            
            translated_parts.append(translated)
    
    print(f"\n✅ Đã dịch {current_part} phần text")
    return ''.join(translated_parts)

def main():
    parser = argparse.ArgumentParser(description="Dịch file README.md")
    parser.add_argument("--source", default="README.md", help="File README nguồn (mặc định: README.md)")
    parser.add_argument("--target", default="en", help="Ngôn ngữ đích: en, vi (mặc định: en)")
    parser.add_argument("--output", help="File output (mặc định: README_{target}.md)")
    parser.add_argument("--from-lang", default="auto", help="Ngôn ngữ nguồn: auto, vi, en (mặc định: auto)")
    
    args = parser.parse_args()
    
    # Kiểm tra thư viện dịch
    if not HAS_DEEP_TRANSLATOR and not HAS_GOOGLETRANS:
        print("❌ Không tìm thấy thư viện dịch!")
        print("📦 Cài đặt một trong các thư viện sau:")
        print("   pip install deep-translator")
        print("   hoặc")
        print("   pip install googletrans==4.0.0rc1")
        sys.exit(1)
    
    # Đọc file
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ Không tìm thấy file: {args.source}")
        sys.exit(1)
    
    print(f"📖 Đọc file: {args.source}")
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Xác định file output
    if args.output:
        output_path = Path(args.output)
    else:
        target_suffix = args.target.upper() if args.target == 'en' else args.target
        output_path = source_path.parent / f"README_{target_suffix}.md"
    
    # Dịch
    print(f"🔄 Bắt đầu dịch...")
    translated_content = translate_markdown(content, args.from_lang, args.target)
    
    # Lưu file
    print(f"💾 Lưu file: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(translated_content)
    
    print(f"✅ Hoàn thành! File đã được lưu tại: {output_path}")

if __name__ == "__main__":
    main()

