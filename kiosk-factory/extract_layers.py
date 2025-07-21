#!/usr/bin/env python3
"""
Zundamon Layer Extraction CLI
コマンドラインからレイヤー抽出を実行するスクリプト
"""

import click
import sys
from pathlib import Path
from layer_extractor import ZundamonLayerExtractor
from colorama import init, Fore, Style
from tqdm import tqdm
import time

# Colorama初期化
init()

@click.command()
@click.option('--psd-path', '-p', default="../assets/zunda.3.2.psd",
              help='PSDファイルのパス')
@click.option('--output-dir', '-o', default="../assets/zundamon_layers",
              help='出力ディレクトリ')
@click.option('--dry-run', '-d', is_flag=True,
              help='実際の抽出を行わず、予測のみ実行')
@click.option('--force', '-f', is_flag=True,
              help='確認なしで実行')
@click.option('--verbose', '-v', is_flag=True,
              help='詳細ログを表示')
def main(psd_path, output_dir, dry_run, force, verbose):
    """
    Zundamon Layer Extractor CLI

    PSDファイルから個別レイヤーを抽出し、静的画像として保存します。
    """

    print(f"{Fore.CYAN}{'='*50}")
    print(f"🎨 Zundamon Layer Extractor")
    print(f"{'='*50}{Style.RESET_ALL}")

    # パスの検証
    psd_file = Path(psd_path)
    if not psd_file.exists():
        print(f"{Fore.RED}❌ Error: PSD file not found: {psd_path}{Style.RESET_ALL}")
        sys.exit(1)

    print(f"{Fore.GREEN}📁 PSD File: {psd_path}")
    print(f"📂 Output Directory: {output_dir}")

    if verbose:
        print(f"🔧 Verbose mode enabled")

    print(f"{Style.RESET_ALL}")

    # 抽出器を初期化
    extractor = ZundamonLayerExtractor(psd_path, output_dir)

    try:
        # Dry-run実行
        print(f"{Fore.YELLOW}🔍 Analyzing PSD structure...{Style.RESET_ALL}")

        with tqdm(desc="Loading PSD", unit="step") as pbar:
            result = extractor.extract_all_layers(dry_run=True)
            pbar.update(1)

        if not result["success"]:
            print(f"{Fore.RED}❌ Analysis failed: {result.get('error', 'Unknown error')}{Style.RESET_ALL}")
            sys.exit(1)

        # 結果表示
        info = result["info"]
        print(f"\n{Fore.CYAN}📊 Analysis Results:{Style.RESET_ALL}")
        print(f"  📄 Total layers: {Fore.YELLOW}{info['total_layers']}{Style.RESET_ALL}")
        print(f"  📦 Radio groups: {Fore.YELLOW}{info['radio_groups']}{Style.RESET_ALL}")
        print(f"  💾 Estimated size: {Fore.YELLOW}{info['estimated_size_mb']} MB{Style.RESET_ALL}")
        print(f"  📁 Output directory: {Fore.YELLOW}{info['output_directory']}{Style.RESET_ALL}")

        if dry_run:
            print(f"\n{Fore.GREEN}✅ Dry-run completed successfully!{Style.RESET_ALL}")
            print(f"{Fore.BLUE}💡 Use --force flag to proceed with actual extraction{Style.RESET_ALL}")
            return

        # 実際の抽出確認
        if not force:
            print(f"\n{Fore.YELLOW}⚠️  This will extract {info['total_layers']} layer images.{Style.RESET_ALL}")
            response = click.confirm("Proceed with extraction?")
            if not response:
                print(f"{Fore.BLUE}🚫 Extraction cancelled.{Style.RESET_ALL}")
                return

        # 実際の抽出実行
        print(f"\n{Fore.GREEN}🚀 Starting layer extraction...{Style.RESET_ALL}")

        start_time = time.time()

        with tqdm(total=info['total_layers'], desc="Extracting layers", unit="layer") as pbar:
            # 抽出実行（プログレスバーは簡易版）
            result = extractor.extract_all_layers(dry_run=False)
            pbar.update(info['total_layers'])

        end_time = time.time()
        duration = end_time - start_time

        if result["success"]:
            print(f"\n{Fore.GREEN}🎉 Extraction completed successfully!{Style.RESET_ALL}")
            print(f"  ✅ Successfully extracted: {Fore.GREEN}{result['extracted']}{Style.RESET_ALL} layers")
            if result['failed'] > 0:
                print(f"  ❌ Failed: {Fore.RED}{result['failed']}{Style.RESET_ALL} layers")
            print(f"  ⏱️  Duration: {Fore.YELLOW}{duration:.2f} seconds{Style.RESET_ALL}")
            print(f"  📄 Metadata saved to: {Fore.BLUE}{result['metadata_path']}{Style.RESET_ALL}")

            # 成功率計算
            total_attempted = result['extracted'] + result['failed']
            success_rate = (result['extracted'] / total_attempted * 100) if total_attempted > 0 else 0
            print(f"  📈 Success rate: {Fore.GREEN}{success_rate:.1f}%{Style.RESET_ALL}")

        else:
            print(f"\n{Fore.RED}❌ Extraction failed: {result.get('error', 'Unknown error')}{Style.RESET_ALL}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Extraction interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}💥 Unexpected error: {e}{Style.RESET_ALL}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
