"""
Health Analytics Engine - 健康指標分析・通知システム
定時実行（10時・15時・20時）で分析結果を生成
ボディリコンプ特化版 - 体脂肪率12%目標・定量ゴール進捗管理
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
import json
from csv_data_integrator import CSVDataIntegrator

class HealthAnalyticsEngine:
    """健康指標分析エンジン - ボディリコンプ特化版"""
    
    def __init__(self, reports_dir: str = None):
        # プロジェクトルートからの絶対パス設定
        if reports_dir is None:
            project_root = Path(__file__).parent
            reports_dir = project_root / "reports"
        self.reports_dir = Path(reports_dir)
        self.integrator = CSVDataIntegrator(str(self.reports_dir))
        
        # 開始日（固定）
        self.start_date = date(2025, 6, 1)
        
        # KGI設定
        self.target_body_fat_rate = 12.0  # 目標体脂肪率12%
        self.target_weekly_calorie_deficit = -1000  # 週-1000kcal目標
        
    def load_latest_data(self) -> pd.DataFrame:
        """最新の7日移動平均データを読み込み（KGI計算用）"""
        ma7_file = self.reports_dir / "7日移動平均データ.csv"
        
        if not ma7_file.exists():
            print("[ERROR] 7日移動平均データが見つかりません")
            return pd.DataFrame()
            
        try:
            df = pd.read_csv(ma7_file, encoding='utf-8-sig')
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            print(f"[INFO] 7日移動平均データ読み込み完了: {len(df)}行 ({df['date'].min().date()} ~ {df['date'].max().date()})")
            return df
        except Exception as e:
            print(f"[ERROR] データ読み込みエラー: {e}")
            return pd.DataFrame()
    def analyze_metabolism_status(self, df: pd.DataFrame) -> dict:
        """代謝状況分析とチートデイ判定"""
        if df.empty:
            return {}
            
        try:
            # 期間別脂肪減少ペース
            fat_loss_28d = self._get_fat_loss_trend(df, 28)
            fat_loss_14d = self._get_fat_loss_trend(df, 14)
            fat_loss_7d = self._get_fat_loss_trend(df, 7)
            
            # 体表温変化（過去7日平均）
            temp_change = self._get_body_temp_change(df, 7)
            
            # 代謝状況判定
            is_fat_loss_stalled = fat_loss_14d is not None and fat_loss_7d is not None and fat_loss_14d <= 0 and fat_loss_7d <= 0
            is_temp_dropping = temp_change is not None and temp_change < -0.1
            
            # チートデイ判定
            days_stalled = self._count_stall_days(df)
            cheat_day_recommended = (days_stalled >= 14 and is_temp_dropping)
            
            return {
                'fat_loss_28d': round(fat_loss_28d, 2) if fat_loss_28d is not None else None,
                'fat_loss_14d': round(fat_loss_14d, 2) if fat_loss_14d is not None else None,
                'fat_loss_7d': round(fat_loss_7d, 2) if fat_loss_7d is not None else None,
                'body_temp_change': round(temp_change, 1) if temp_change is not None else None,
                'metabolism_status': 'stopped' if is_fat_loss_stalled else 'normal',
                'cheat_day_recommended': cheat_day_recommended,
                'stall_days': days_stalled
            }
            
        except Exception as e:
            print(f"[ERROR] 代謝状況分析エラー: {e}")
            return {}
            
    def _get_fat_loss_trend(self, df: pd.DataFrame, days: int) -> float:
        """指定期間の脂肪減少トレンド計算（適切な移動平均使用）"""
        # 適切な移動平均列を選択
        if days == 28:
            col_name = '体脂肪量_kg_ma28'
        elif days == 14:
            col_name = '体脂肪量_kg_ma14'
        else:  # 7日間
            col_name = '体脂肪量_kg_ma7'
        
        valid_data = df.dropna(subset=[col_name])
        
        if len(valid_data) < days:
            return None
            
        # 現在の移動平均値 vs days日前の移動平均値
        current_value = valid_data.iloc[-1][col_name]
        past_value = valid_data.iloc[-days][col_name]
        return current_value - past_value
        
    def _get_body_temp_change(self, df: pd.DataFrame, days: int) -> float:
        """体表温変化計算（Oura Ring体表温偏差データ使用）"""
        period_data = df.tail(days)
        
        # 体表温偏差データを使用（絶対値ではなく偏差で判定）
        valid_temp_deviation = period_data.dropna(subset=['体表温偏差_celsius'])
        valid_temp_trend = period_data.dropna(subset=['体表温トレンド_celsius'])
        
        # 体表温偏差データが利用可能な場合
        if len(valid_temp_deviation) >= 2:
            recent_deviation = valid_temp_deviation.tail(3)['体表温偏差_celsius'].mean()
            baseline_deviation = valid_temp_deviation.head(3)['体表温偏差_celsius'].mean()
            return recent_deviation - baseline_deviation
        
        # 体表温トレンドデータが利用可能な場合
        elif len(valid_temp_trend) >= 2:
            recent_trend = valid_temp_trend.tail(3)['体表温トレンド_celsius'].mean()
            baseline_trend = valid_temp_trend.head(3)['体表温トレンド_celsius'].mean()
            return recent_trend - baseline_trend
        
        else:
            return None
        
    def _count_stall_days(self, df: pd.DataFrame) -> int:
        """脂肪減少停滞日数カウント"""
        # 簡易実装：過去14日で脂肪量変化がほぼ0の場合
        valid_data = df.dropna(subset=['体脂肪量_kg_ma14'])
        
        if len(valid_data) < 14:
            return 0
            
        # 現在の14日移動平均 vs 14日前の14日移動平均
        current_fat = valid_data.iloc[-1]['体脂肪量_kg_ma14']
        past_fat = valid_data.iloc[-14]['体脂肪量_kg_ma14']
        fat_change = abs(current_fat - past_fat)
        return 14 if fat_change < 0.1 else 0
        
    def calculate_calorie_adjustment(self, current_7d_balance: float, current_14d_balance: float) -> dict:
        """カロリー調整計算と運動量換算"""
        target_7d = self.target_weekly_calorie_deficit  # -1000kcal
        
        deficit_7d = current_7d_balance - target_7d
        deficit_14d = current_14d_balance - (target_7d * 2)  # 14日間は-2000kcal目標
        
        daily_adjustment_needed = deficit_7d / 7
        
        # 運動量換算
        exercise_options = {
            'jogging_minutes': abs(daily_adjustment_needed) / 10,      # 10kcal/分
            'walking_minutes': abs(daily_adjustment_needed) / 5,       # 5kcal/分
            'strength_minutes': abs(daily_adjustment_needed) / 9       # 9kcal/分
        }
        
        return {
            'deficit_7d': round(deficit_7d, 0),
            'deficit_14d': round(deficit_14d, 0),
            'daily_adjustment': round(daily_adjustment_needed, 0),
            'exercise_options': {k: round(v, 0) for k, v in exercise_options.items()}
        }
        """総合成績計算（開始～現在）"""
        if df.empty:
            return {}
            
        try:
            # 有効データの最初と最後を使用（nanを除外）
            valid_data = df.dropna(subset=['体重_kg_ma7', '体脂肪率_ma7', '筋肉量_kg_ma7'])
            
            if len(valid_data) < 2:
                print("[WARNING] 有効データが不足しています")
                return {}
                
            start_data = valid_data.iloc[0]
            latest_data = valid_data.iloc[-1]
            
            # 体重変化（追加）
            weight_start = start_data.get('体重_kg_ma7', 0)
            weight_latest = latest_data.get('体重_kg_ma7', 0)
            weight_change = weight_latest - weight_start
            
            # 体脂肪率変化
            bf_rate_start = start_data.get('体脂肪率_ma7', 0)
            bf_rate_latest = latest_data.get('体脂肪率_ma7', 0)
            bf_rate_change = bf_rate_latest - bf_rate_start
            
            # 体脂肪量変化
            bf_mass_start = start_data.get('体脂肪量_kg_ma7', 0)
            bf_mass_latest = latest_data.get('体脂肪量_kg_ma7', 0)
            bf_mass_change = bf_mass_latest - bf_mass_start
            
            # 筋肉量変化
            muscle_start = start_data.get('筋肉量_kg_ma7', 0)
            muscle_latest = latest_data.get('筋肉量_kg_ma7', 0)
            muscle_change = muscle_latest - muscle_start
            
            # 期間計算
            days_total = (latest_data['date'].date() - start_data['date'].date()).days
            
            return {
                'analysis_date': latest_data['date'].strftime('%Y-%m-%d'),
                'start_date': start_data['date'].strftime('%Y-%m-%d'),
                'period_days': days_total,
                'weight_start': round(weight_start, 2),
                'weight_latest': round(weight_latest, 2),
                'weight_change': round(weight_change, 2),
                'body_fat_rate_start': round(bf_rate_start, 1),
                'body_fat_rate_latest': round(bf_rate_latest, 1),
                'body_fat_rate_change': round(bf_rate_change, 1),
                'body_fat_mass_start': round(bf_mass_start, 2),
                'body_fat_mass_latest': round(bf_mass_latest, 2),
                'body_fat_mass_change': round(bf_mass_change, 2),
                'muscle_mass_start': round(muscle_start, 2),
                'muscle_mass_latest': round(muscle_latest, 2),
                'muscle_mass_change': round(muscle_change, 2)
            }
            
        except Exception as e:
            print(f"[ERROR] 総合成績計算エラー: {e}")
            return {}
            
    def calculate_kgi_progress(self, df: pd.DataFrame) -> dict:
        """KGI進捗計算（体脂肪率12%目標）"""
        if df.empty:
            return {}
            
        try:
            # 7日移動平均データから体脂肪率を取得
            valid_data = df.dropna(subset=['体脂肪率_ma7'])
            
            if len(valid_data) < 2:
                print("[WARNING] 体脂肪率データが不足しています")
                return {}
                
            start_data = valid_data.iloc[0]
            latest_data = valid_data.iloc[-1]
            
            start_bf_rate = start_data.get('体脂肪率_ma7', 0)
            current_bf_rate = latest_data.get('体脂肪率_ma7', 0)
            
            # 進捗計算
            total_reduction_needed = start_bf_rate - self.target_body_fat_rate  # 6.8%
            achieved_reduction = start_bf_rate - current_bf_rate  # 1.1%
            progress_rate = (achieved_reduction / total_reduction_needed) * 100 if total_reduction_needed > 0 else 0
            
            # 週間平均減少率計算（過去4週間）
            weeks_data = valid_data.tail(28)  # 過去28日≈4週間
            if len(weeks_data) >= 2:
                weeks_elapsed = (weeks_data.iloc[-1]['date'] - weeks_data.iloc[0]['date']).days / 7
                total_reduction = weeks_data.iloc[0]['体脂肪率_ma7'] - weeks_data.iloc[-1]['体脂肪率_ma7']
                weekly_reduction_rate = total_reduction / weeks_elapsed if weeks_elapsed > 0 else 0
            else:
                weekly_reduction_rate = 0
                
            # 到達予測日計算
            remaining_reduction = current_bf_rate - self.target_body_fat_rate
            if weekly_reduction_rate > 0:
                weeks_needed = remaining_reduction / weekly_reduction_rate
                target_date = datetime.now() + timedelta(weeks=weeks_needed)
                target_date_str = target_date.strftime('%Y年%m月%d日')
            else:
                target_date_str = "現在のペースでは到達困難"
                
            # プログレスバー生成
            progress_bar = self._generate_progress_bar(progress_rate)
            
            return {
                'analysis_date': latest_data['date'].strftime('%Y-%m-%d'),
                'start_bf_rate': round(start_bf_rate, 1),
                'current_bf_rate': round(current_bf_rate, 1),
                'target_bf_rate': self.target_body_fat_rate,
                'reduction_achieved': round(achieved_reduction, 1),
                'total_reduction_needed': round(total_reduction_needed, 1),
                'progress_rate': round(progress_rate, 1),
                'progress_bar': progress_bar,
                'weekly_reduction_rate': round(weekly_reduction_rate, 3),
                'target_date': target_date_str
            }
            
        except Exception as e:
            print(f"[ERROR] KGI進捗計算エラー: {e}")
            return {}
            
    def _generate_progress_bar(self, progress_rate: float, bar_length: int = 20) -> str:
        """プログレスバー生成"""
        filled_length = int(bar_length * progress_rate / 100)
        half_filled = 1 if (bar_length * progress_rate / 100) - filled_length >= 0.5 else 0
        
        bar = '█' * filled_length
        if half_filled and filled_length < bar_length:
            bar += '▌'
            empty_length = bar_length - filled_length - 1
        else:
            empty_length = bar_length - filled_length
            
        bar += '░' * empty_length
        
        return f"[{bar}] {progress_rate:.1f}% / 100%"
            
    def calculate_period_performance(self, df: pd.DataFrame, days: int) -> dict:
        """期間成績計算（指定日数間）- 移動平均列使用版"""
        if df.empty:
            return {}
            
        try:
            # 移動平均列の選択
            if days == 28:
                fat_col = '体脂肪量_kg_ma28'
                muscle_col = '筋肉量_kg_ma28'
            elif days == 14:
                fat_col = '体脂肪量_kg_ma14'
                muscle_col = '筋肉量_kg_ma14'
            else:  # 7日間
                fat_col = '体脂肪量_kg_ma7'
                muscle_col = '筋肉量_kg_ma7'
            
            # 有効データのみで計算
            valid_bf_data = df.dropna(subset=[fat_col])
            valid_muscle_data = df.dropna(subset=[muscle_col])
            
            # 体脂肪量・筋肉量変化計算（移動平均の変化）
            bf_mass_change = None
            bf_reduction_rate = None
            muscle_mass_change = None
            muscle_rate = None
            
            if len(valid_bf_data) >= days:
                # 現在の移動平均値 vs days日前の移動平均値
                current_bf = valid_bf_data.iloc[-1][fat_col]
                past_bf = valid_bf_data.iloc[-days][fat_col]
                bf_mass_change = current_bf - past_bf
                bf_reduction_rate = bf_mass_change / days
                
            if len(valid_muscle_data) >= days:
                # 現在の移動平均値 vs days日前の移動平均値
                current_muscle = valid_muscle_data.iloc[-1][muscle_col]
                past_muscle = valid_muscle_data.iloc[-days][muscle_col]
                muscle_mass_change = current_muscle - past_muscle
                muscle_rate = muscle_mass_change / days
            
            # カロリー関連計算（直近days日分）
            period_df = df.tail(days)
            cal_balance_total = period_df['カロリー収支_kcal'].sum()
            cal_balance_avg = period_df['カロリー収支_kcal'].mean()
            
            # 摂取・消費カロリー合計（新規追加）
            total_intake = period_df['摂取カロリー_kcal'].sum()
            total_consumed = period_df['消費カロリー_kcal'].sum()
            
            return {
                'period_days': days,
                'actual_data_days': len(period_df),
                'body_fat_mass_change': round(bf_mass_change, 2) if bf_mass_change is not None else None,
                'body_fat_reduction_rate_per_day': round(bf_reduction_rate, 3) if bf_reduction_rate is not None else None,
                'muscle_mass_change': round(muscle_mass_change, 2) if muscle_mass_change is not None else None,
                'muscle_rate_per_day': round(muscle_rate, 3) if muscle_rate is not None else None,
                'calorie_balance_total': round(cal_balance_total, 0),
                'calorie_balance_avg': round(cal_balance_avg, 1),
                'total_intake_calories': round(total_intake, 0),
                'total_consumed_calories': round(total_consumed, 0)
            }
            
        except Exception as e:
            print(f"[ERROR] {days}日間成績計算エラー: {e}")
            return {}
            
    def generate_analysis_report(self) -> dict:
        """ボディリコンプ特化分析レポート生成"""
        print("=== ボディリコンプ分析開始 ===")
        
        # データ読み込み
        df = self.load_latest_data()
        if df.empty:
            return {}
            
        # KGI進捗分析
        kgi_progress = self.calculate_kgi_progress(df)
        
        # 期間別分析（既存）
        days28_perf = self.calculate_period_performance(df, 28)
        days14_perf = self.calculate_period_performance(df, 14)
        days7_perf = self.calculate_period_performance(df, 7)
        
        # 代謝状況分析
        metabolism = self.analyze_metabolism_status(df)
        
        # カロリー調整計算
        calorie_adj = self.calculate_calorie_adjustment(
            days7_perf.get('calorie_balance_total', 0),
            days14_perf.get('calorie_balance_total', 0)
        )
        
        # レポート統合
        report = {
            'generated_at': datetime.now().isoformat(),
            'data_period': {
                'start_date': self.start_date.isoformat(),
                'end_date': df['date'].max().strftime('%Y-%m-%d'),
                'total_days': len(df)
            },
            'kgi_progress': kgi_progress,
            'last_28days': days28_perf,
            'last_14days': days14_perf,
            'last_7days': days7_perf,
            'metabolism_analysis': metabolism,
            'calorie_adjustment': calorie_adj
        }
        
        print("[SUCCESS] ボディリコンプ分析レポート生成完了")
        return report
        
    def format_notification_message(self, report: dict) -> str:
        """新カード式レポートフォーマット"""
        if not report:
            return "データ分析に失敗しました。"
            
        try:
            # データ読み込み
            df = self.load_latest_data()
            
            kgi = report.get('kgi_progress', {})
            days28 = report.get('last_28days', {})
            days14 = report.get('last_14days', {})
            days7 = report.get('last_7days', {})
            metabolism = report.get('metabolism_analysis', {})
            calorie_adj = report.get('calorie_adjustment', {})
            
            timestamp = datetime.now().strftime("%m/%d %H:%M")
            
            # 体脂肪率変化計算（28日/14日/7日）
            bf_changes = self._calculate_bf_rate_changes(df)
            
            # 今日のカロリー収支予測
            today_cal_prediction = self._calculate_today_calorie_prediction(df)
            
            # PFCバランス計算
            pfc_analysis = self._calculate_pfc_balance(df)
            
            # 食物繊維計算
            fiber_analysis = self._calculate_fiber_intake(df)
            
            # 目標到達予測
            target_prediction = self._calculate_target_prediction(bf_changes)
            
            # 新フォーマットメッセージ生成
            message = f"""🎯 体脂肪率進捗 | {timestamp}

🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜ {kgi.get('progress_rate', 0):.1f}%

📍現在: {kgi.get('current_bf_rate', 0)}%  🎯目標: {kgi.get('target_bf_rate', 12):.1f}%
📈28日: {bf_changes['bf_28d']:+.1f}%  14日: {bf_changes['bf_14d']:+.1f}%  7日: {bf_changes['bf_7d']:+.1f}%
🗓️ 予測: {target_prediction}


📊 体組成変化トレンド

🔥 体脂肪量変化
   28日: {self._format_change_safe(metabolism.get('fat_loss_28d'))}kg  14日: {self._format_change_safe(metabolism.get('fat_loss_14d'))}kg  7日: {self._format_change_safe(metabolism.get('fat_loss_7d'))}kg
   判定: {self._get_fat_loss_status_emoji(metabolism)}

💪 筋肉量変化  
   28日: {days28.get('muscle_mass_change', 0):+.2f}kg  14日: {days14.get('muscle_mass_change', 0):+.2f}kg  7日: {days7.get('muscle_mass_change', 0):+.2f}kg
   判定: {self._get_muscle_status_emoji(days7.get('muscle_mass_change', 0))}

🌡️ 代謝状況
   体表温変化: {self._format_change_safe(metabolism.get('body_temp_change'))}°C
   判定: {self._get_metabolism_status_emoji(metabolism)}


🍽️ PFCバランス（7日平均）

{pfc_analysis['pfc_line']}
理想: P25% F68% C7%（ケトジェニック）
判定: {pfc_analysis['judgment']}

📊 食物繊維: {fiber_analysis['fiber_avg']:.0f}g/日 (目標25g以上) {fiber_analysis['status']}


⚖️ カロリー収支

🔴 7日間: {days7.get('calorie_balance_total', 0):+.0f}kcal超過
   {self._calculate_estimated_fat_change(days7.get('calorie_balance_total', 0))}
🔴 14日間: {days14.get('calorie_balance_total', 0):+.0f}kcal超過
   {self._calculate_estimated_fat_change(days14.get('calorie_balance_total', 0))}
🔴 28日間: {days28.get('calorie_balance_total', 0):+.0f}kcal超過
   {self._calculate_estimated_fat_change(days28.get('calorie_balance_total', 0))}

過去7日間のカロリー収支
{today_cal_prediction}

🔥 チートデイ: {'YES' if metabolism.get('cheat_day_recommended', False) else 'NO'}（停滞のため）"""

            return message
            
        except Exception as e:
            print(f"[ERROR] 新フォーマットメッセージ生成エラー: {e}")
            return "レポート生成に失敗しました。"
            
    def _calculate_estimated_fat_change(self, calorie_balance: float) -> str:
        """カロリー収支から推定脂肪増減量を計算（脂肪1kg = 7200kcal）"""
        if calorie_balance == 0:
            return "±0.00kg"
        
        fat_change_kg = calorie_balance / 7200
        
        if fat_change_kg > 0:
            return f"推定脂肪増加: +{fat_change_kg:.2f}kg"
        else:
            return f"推定脂肪減少: {fat_change_kg:.2f}kg"
    
    def _format_change_safe(self, value) -> str:
        """変化量を安全にフォーマット（None対応）"""
        if value is None:
            return "データ不足"
        return f"{value:+.2f}"
        
    def _get_fat_loss_status_emoji(self, metabolism: dict) -> str:
        """脂肪減少状況の絵文字判定"""
        fat_loss_7d = metabolism.get('fat_loss_7d', 0)
        fat_loss_14d = metabolism.get('fat_loss_14d', 0)
        
        if fat_loss_7d is None or fat_loss_14d is None:
            return "📊 データ蓄積中"
        
        if fat_loss_14d <= 0 and fat_loss_7d <= 0:
            return "停滞中 🔴"
        elif fat_loss_7d < -0.2:
            return "順調 ✅"
        else:
            return "緩やか 🟡"
            
    def _get_metabolism_status_emoji(self, metabolism: dict) -> str:
        """代謝状況の絵文字判定"""
        temp_change = metabolism.get('body_temp_change')
        
        if temp_change is None:
            return "データ不足 📊"
        elif temp_change < -0.2:
            return "代謝低下の可能性 🟡"
        elif temp_change < -0.1:
            return "要注意 🟡"
        else:
            return "✅"
            
    def _get_fat_burn_status_emoji(self, metabolism: dict) -> str:
        """脂肪燃焼状況の絵文字"""
        if metabolism.get('metabolism_status') == 'stopped':
            return "🔴"
        else:
            return "✅"
            
    def _get_fat_burn_status_text(self, metabolism: dict) -> str:
        """脂肪燃焼状況のテキスト"""
        if metabolism.get('metabolism_status') == 'stopped':
            return "完全停滞"
        else:
            return "維持中"
            
    def _get_metabolism_status_text(self, metabolism: dict) -> str:
        """代謝効率のテキスト"""
        temp_change = metabolism.get('body_temp_change')
        
        if temp_change is None:
            return "データ不足"
        elif temp_change < -0.2:
            return "低下傾向"
        else:
            return "安定"
            
    def _get_cheat_day_reason(self, metabolism: dict) -> str:
        """チートデイ推奨理由"""
        if metabolism.get('cheat_day_recommended', False):
            return "理由: 脂肪停滞2週間 + 体表温低下"
        else:
            return "理由: 現状維持で経過観察"
            
    def _calculate_bf_rate_changes(self, df) -> dict:
        """体脂肪率の28/14/7日変化を計算（適切な移動平均使用）"""
        try:
            # 各期間の移動平均データ確認
            valid_ma7 = df.dropna(subset=['体脂肪率_ma7'])
            valid_ma14 = df.dropna(subset=['体脂肪率_ma14']) 
            valid_ma28 = df.dropna(subset=['体脂肪率_ma28'])
            
            bf_28d = 0.0
            bf_14d = 0.0  
            bf_7d = 0.0
            
            # 28日移動平均変化
            if len(valid_ma28) >= 28:
                current_bf_28 = valid_ma28.iloc[-1]['体脂肪率_ma28']
                past_bf_28 = valid_ma28.iloc[-28]['体脂肪率_ma28']
                bf_28d = current_bf_28 - past_bf_28
            
            # 14日移動平均変化
            if len(valid_ma14) >= 14:
                current_bf_14 = valid_ma14.iloc[-1]['体脂肪率_ma14']
                past_bf_14 = valid_ma14.iloc[-14]['体脂肪率_ma14']
                bf_14d = current_bf_14 - past_bf_14
            
            # 7日移動平均変化
            if len(valid_ma7) >= 7:
                current_bf_7 = valid_ma7.iloc[-1]['体脂肪率_ma7']
                past_bf_7 = valid_ma7.iloc[-7]['体脂肪率_ma7']
                bf_7d = current_bf_7 - past_bf_7
                
            return {'bf_28d': bf_28d, 'bf_14d': bf_14d, 'bf_7d': bf_7d}
            
        except Exception as e:
            print(f"[ERROR] 体脂肪率変化計算エラー: {e}")
            return {'bf_28d': 0.0, 'bf_14d': 0.0, 'bf_7d': 0.0}
    
    def _calculate_today_calorie_prediction(self, df) -> str:
        """過去7日間のカロリー収支詳細リストを作成"""
        try:
            from datetime import datetime, timedelta
            
            # 現在の日付を取得（実際の今日）
            today = datetime.now().date()
            
            calorie_lines = []
            
            # 過去7日間（今日から7日前まで）を順番に処理
            for i in range(7):
                target_date = today - timedelta(days=i)
                target_date_str = target_date.strftime('%Y-%m-%d')
                
                # 該当日のデータをCSVから検索
                target_row = df[df['date'] == target_date_str]
                
                if not target_row.empty:
                    # データがある場合
                    balance = target_row['カロリー収支_kcal'].iloc[0]
                    weekday_jp = ['月', '火', '水', '木', '金', '土', '日'][target_date.weekday()]
                    formatted_date = target_date.strftime('%m/%d')
                    
                    calorie_line = f"{formatted_date} {weekday_jp}: {balance:+.0f}kcal"
                    calorie_lines.append(calorie_line)
                else:
                    # データがない場合
                    weekday_jp = ['月', '火', '水', '木', '金', '土', '日'][target_date.weekday()]
                    formatted_date = target_date.strftime('%m/%d')
                    
                    calorie_line = f"{formatted_date} {weekday_jp}: データなし"
                    calorie_lines.append(calorie_line)
            
            return "\n".join(calorie_lines)
            
        except Exception as e:
            print(f"[ERROR] カロリー収支リスト作成エラー: {e}")
            return "計算エラー"
            
    def _calculate_pfc_balance(self, df) -> dict:
        """PFCバランス計算（ケトジェニック仕様）"""
        try:
            # 過去7日間のPFCデータ取得
            recent_7days = df.tail(8).head(7)
            
            # 平均値計算
            avg_protein = recent_7days['タンパク質_g'].mean()
            avg_fat = recent_7days['脂質_g'].mean()
            avg_carb = recent_7days['糖質_g'].mean()
            
            # カロリー換算（P:4kcal/g, F:9kcal/g, C:4kcal/g）
            protein_kcal = avg_protein * 4
            fat_kcal = avg_fat * 9
            carb_kcal = avg_carb * 4
            total_kcal = protein_kcal + fat_kcal + carb_kcal
            
            if total_kcal == 0:
                return {
                    'pfc_line': "P: 0g (0%) F: 0g (0%) C: 0g (0%)",
                    'judgment': "データ不足 📊"
                }
            
            # 比率計算
            protein_pct = (protein_kcal / total_kcal) * 100
            fat_pct = (fat_kcal / total_kcal) * 100
            carb_pct = (carb_kcal / total_kcal) * 100
            
            # PFCライン生成
            pfc_line = f"P: {avg_protein:.0f}g ({protein_pct:.0f}%) F: {avg_fat:.0f}g ({fat_pct:.0f}%) C: {avg_carb:.0f}g ({carb_pct:.0f}%)"
            
            # ケトジェニック判定（理想：P25% F68% C7%）
            judgments = []
            if abs(protein_pct - 25) > 5:
                if protein_pct < 25:
                    judgments.append("P不足 🟡")
                else:
                    judgments.append("P過多 🟡")
            
            if abs(fat_pct - 68) > 10:
                if fat_pct < 68:
                    judgments.append("F不足 🟡")
                else:
                    judgments.append("F過多 🟡")
            
            if abs(carb_pct - 7) > 5:
                if carb_pct > 7:
                    judgments.append("C過多 🔴")
                else:
                    judgments.append("C不足 🟡")
            
            if not judgments:
                judgment = "ケトジェニック最適 ✅"
            else:
                judgment = " ".join(judgments)
            
            return {'pfc_line': pfc_line, 'judgment': judgment}
            
        except Exception as e:
            print(f"[ERROR] PFCバランス計算エラー: {e}")
            return {
                'pfc_line': "P: 0g (0%) F: 0g (0%) C: 0g (0%)",
                'judgment': "計算エラー 📊"
            }
            
    def _calculate_fiber_intake(self, df) -> dict:
        """食物繊維摂取量計算"""
        try:
            # 過去7日間の食物繊維平均
            recent_7days = df.tail(8).head(7)
            avg_fiber = recent_7days['食物繊維_g'].mean()
            
            if pd.isna(avg_fiber) or avg_fiber == 0:
                return {'fiber_avg': 0, 'status': '📊'}
            
            # 目標25g以上での判定
            if avg_fiber >= 25:
                status = "✅"
            elif avg_fiber >= 20:
                status = "🟡"
            else:
                status = "🔴"
                
            return {'fiber_avg': avg_fiber, 'status': status}
            
        except Exception as e:
            print(f"[ERROR] 食物繊維計算エラー: {e}")
            return {'fiber_avg': 0, 'status': '📊'}
    
    def _calculate_target_prediction(self, bf_changes: dict) -> str:
        """目標到達予測計算"""
        try:
            # 最近の変化ペースで判定
            recent_change_7d = bf_changes['bf_7d']
            recent_change_14d = bf_changes['bf_14d']
            
            # 停滞・悪化判定
            if recent_change_7d >= 0 and recent_change_14d >= 0:
                return "現在のペースでは到達困難"
            
            # 変化ペースから予測（7日間のペースを優先）
            if recent_change_7d < -0.3:  # 週0.3%以上減少
                weeks_needed = 5.7 / abs(recent_change_7d)  # 残り5.7%
                months_needed = weeks_needed / 4.3
                if months_needed < 12:
                    return f"約{months_needed:.1f}ヶ月で到達"
                else:
                    return f"約{months_needed/12:.1f}年で到達"
            elif recent_change_7d < 0:  # 緩やかな減少
                return "緩やかペース（要改善）"
            else:
                return "現在のペースでは到達困難"
                
        except Exception as e:
            print(f"[ERROR] 目標予測計算エラー: {e}")
            return "計算エラー"
    
    def _get_muscle_status_emoji(self, muscle_change: float) -> str:
        """筋肉量変化のステータス絵文字"""
        if muscle_change > 0.2:
            return "増量中 ✅"
        elif muscle_change >= -0.1:
            return "維持中 ✅"
        elif muscle_change >= -0.3:
            return "やや減少 🟡"
        else:
            return "減少中 🔴"
            
    def save_analysis_report(self, report: dict, filename: str = None):
        """分析レポートをJSONで保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_report_{timestamp}.json"
            
        reports_file = self.reports_dir / filename
        
        try:
            with open(reports_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            print(f"[SUCCESS] 分析レポート保存: {filename}")
        except Exception as e:
            print(f"[ERROR] レポート保存エラー: {e}")
            
    def run_scheduled_analysis(self) -> dict:
        """定時分析実行（10時・15時・20時用）"""
        print(f"=== 定時分析実行 {datetime.now().strftime('%H:%M:%S')} ===")
        
        # 最新HAEデータを統合
        print("[STEP1] 最新HAEデータ統合...")
        integration_result = self.integrator.process_latest_hae_data()
        
        if not integration_result:
            print("[WARNING] HAEデータ統合に失敗しましたが、既存データで分析続行")
            
        # 分析実行
        print("[STEP2] 健康指標分析...")
        report = self.generate_analysis_report()
        
        if report:
            # レポート保存
            self.save_analysis_report(report)
            
            # 通知メッセージ生成（テスト時は出力しない）
            print("\n=== 通知メッセージ ===")
            print("ボディリコンプ進捗レポート生成完了")
            print(f"体脂肪率: {report.get('kgi_progress', {}).get('current_bf_rate', 0)}%")
            print(f"目標到達予定: {report.get('kgi_progress', {}).get('target_date', '計算中')}")
            
        return report
        
    def test_analysis(self):
        """分析機能テスト"""
        print("=== 分析機能テスト ===")
        return self.run_scheduled_analysis()

if __name__ == "__main__":
    analytics = HealthAnalyticsEngine()
    analytics.test_analysis()
