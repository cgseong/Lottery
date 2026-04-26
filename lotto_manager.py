import json
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

class LottoManager:
    def __init__(self, data_file: str = 'lotto_tickets.json'):
        self.data_file = data_file
        self.tickets = self._load_tickets()
        
    def _load_tickets(self) -> Dict:
        """저장된 티켓 데이터를 로드합니다."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {'tickets': [], 'statistics': self._init_statistics()}
        return {'tickets': [], 'statistics': self._init_statistics()}
    
    def _init_statistics(self) -> Dict:
        """통계 데이터 초기화"""
        return {
            'total_investment': 0,
            'total_prize': 0,
            'total_tickets': 0,
            'winning_tickets': 0,
            'roi': 0.0
        }
    
    def _save_tickets(self):
        """티켓 데이터를 파일에 저장합니다."""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.tickets, f, ensure_ascii=False, indent=2)
    
    def add_ticket(self, numbers: List[int], purchase_date: str, purchase_amount: int = 1000) -> bool:
        """새로운 티켓을 추가합니다."""
        if len(numbers) != 6 or not all(1 <= n <= 45 for n in numbers):
            return False
            
        ticket = {
            'id': len(self.tickets['tickets']) + 1,
            'numbers': sorted(numbers),
            'purchase_date': purchase_date,
            'purchase_amount': purchase_amount,
            'prize_amount': 0,
            'is_checked': False,
            'winning_rank': None
        }
        
        self.tickets['tickets'].append(ticket)
        self.tickets['statistics']['total_investment'] += purchase_amount
        self.tickets['statistics']['total_tickets'] += 1
        self._save_tickets()
        return True
    
    def check_winning(self, ticket_id: int, winning_numbers: List[int], bonus_number: int) -> Optional[Dict]:
        """티켓의 당첨 여부를 확인합니다."""
        for ticket in self.tickets['tickets']:
            if ticket['id'] == ticket_id:
                matched = len(set(ticket['numbers']) & set(winning_numbers))
                has_bonus = bonus_number in ticket['numbers']
                
                # 당첨 등수 및 금액 계산
                prize_info = self._calculate_prize(matched, has_bonus)
                ticket['prize_amount'] = prize_info['amount']
                ticket['winning_rank'] = prize_info['rank']
                ticket['is_checked'] = True
                
                if prize_info['amount'] > 0:
                    self.tickets['statistics']['total_prize'] += prize_info['amount']
                    self.tickets['statistics']['winning_tickets'] += 1
                
                self._update_statistics()
                self._save_tickets()
                return prize_info
        return None
    
    def _calculate_prize(self, matched: int, has_bonus: bool) -> Dict:
        """당첨 등수와 금액을 계산합니다."""
        if matched == 6:
            return {'rank': 1, 'amount': 2000000000}  # 1등 (예시 금액)
        elif matched == 5 and has_bonus:
            return {'rank': 2, 'amount': 50000000}    # 2등 (예시 금액)
        elif matched == 5:
            return {'rank': 3, 'amount': 1500000}     # 3등 (예시 금액)
        elif matched == 4:
            return {'rank': 4, 'amount': 50000}       # 4등 (예시 금액)
        elif matched == 3:
            return {'rank': 5, 'amount': 5000}        # 5등 (예시 금액)
        return {'rank': None, 'amount': 0}
    
    def _update_statistics(self):
        """통계 정보를 업데이트합니다."""
        stats = self.tickets['statistics']
        if stats['total_investment'] > 0:
            stats['roi'] = (stats['total_prize'] - stats['total_investment']) / stats['total_investment'] * 100
    
    def get_statistics(self) -> Dict:
        """현재 통계 정보를 반환합니다."""
        return self.tickets['statistics']
    
    def get_tickets(self, include_checked: bool = True) -> List[Dict]:
        """저장된 티켓 목록을 반환합니다."""
        if include_checked:
            return self.tickets['tickets']
        return [t for t in self.tickets['tickets'] if not t['is_checked']]
    
    def get_ticket_by_id(self, ticket_id: int) -> Optional[Dict]:
        """특정 ID의 티켓 정보를 반환합니다."""
        for ticket in self.tickets['tickets']:
            if ticket['id'] == ticket_id:
                return ticket
        return None
    
    def register_user(self, username: str, password: str) -> bool:
        """새로운 사용자를 등록합니다."""
        users_file = 'users.json'

        # 사용자 데이터 로드
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as f:
                try:
                    users = json.load(f)
                except json.JSONDecodeError:
                    users = {}
        else:
            users = {}

        # 사용자 이름 중복 확인
        if username in users:
            return False

        # 사용자 등록
        users[username] = {
            'password': self._hash_password(password),  # 실제로는 해싱된 비밀번호를 저장해야 함
            'created_at': datetime.now().isoformat()
        }

        # 사용자 데이터 저장
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

        return True

    def _hash_password(self, password: str) -> str:
        """Hash password with PBKDF2-HMAC-SHA256."""
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000,
        )
        return f"pbkdf2_sha256$100000${salt.hex()}${digest.hex()}"
