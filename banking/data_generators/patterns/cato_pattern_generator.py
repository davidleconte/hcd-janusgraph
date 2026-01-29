"""
Coordinated Account Takeover (CATO) Pattern Generator

Generates sophisticated coordinated account takeover patterns including:
- Simultaneous login attempts across multiple accounts
- Velocity-based anomalies (rapid succession of activities)
- Device fingerprinting mismatches
- IP address analysis and geolocation anomalies
- Behavioral pattern deviations
- Credential stuffing attacks
- Session hijacking patterns

Business Context:
Account takeover fraud involves criminals gaining unauthorized access to customer
accounts through various means (phishing, credential theft, malware). Coordinated
attacks target multiple accounts simultaneously, often using automated tools.

Detection Indicators:
- Multiple failed login attempts followed by success
- Login from unusual locations/devices
- Rapid account changes after login
- Unusual transaction patterns post-takeover
- Multiple accounts accessed from same IP/device
- Time-of-day anomalies
- Behavioral biometric deviations
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import random

from ..utils.data_models import (
    Person, Account, Transaction, Communication,
    Pattern, RiskLevel
)
from ..utils.helpers import (
    random_date_between, random_amount
)
from ..core.base_generator import BaseGenerator
from ..core.person_generator import PersonGenerator
from ..core.account_generator import AccountGenerator
from ..events.transaction_generator import TransactionGenerator
from ..events.communication_generator import CommunicationGenerator


class CATOPatternGenerator(BaseGenerator[Pattern]):
    """
    Generator for Coordinated Account Takeover (CATO) patterns.
    
    Simulates sophisticated account takeover attacks with multiple
    coordinated indicators and behavioral anomalies.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize CATO pattern generator."""
        super().__init__(seed)
        self.person_gen = PersonGenerator(seed)
        self.account_gen = AccountGenerator(seed)
        self.transaction_gen = TransactionGenerator(seed)
        self.communication_gen = CommunicationGenerator(seed)
    
    def generate(
        self,
        pattern_type: str = "credential_stuffing",
        victim_count: int = 5,
        attacker_count: int = 2,
        start_date: Optional[datetime] = None,
        duration_days: int = 7,
        **kwargs
    ) -> Pattern:
        """
        Generate a coordinated account takeover pattern.
        
        Args:
            pattern_type: Type of CATO attack
                - "credential_stuffing": Automated credential testing
                - "session_hijacking": Session token theft
                - "sim_swap": SIM card swap attack
                - "phishing_campaign": Coordinated phishing
                - "malware_based": Malware-facilitated takeover
            victim_count: Number of victim accounts (2-20)
            attacker_count: Number of attackers (1-5)
            start_date: Pattern start date
            duration_days: Pattern duration (1-30 days)
            
        Returns:
            Pattern object with CATO indicators
        """
        # Ensure start_date is not None
        from datetime import date as date_type
        if start_date is None:
            days_back = 90
            end = date_type.today()
            start = end - timedelta(days=days_back)
            actual_start_date = datetime.combine(random_date_between(start, end), datetime.min.time())
        else:
            actual_start_date = start_date
        end_date = actual_start_date + timedelta(days=duration_days)
        
        # Generate pattern based on type
        if pattern_type == "credential_stuffing":
            return self._generate_credential_stuffing(
                victim_count, attacker_count, actual_start_date, end_date
            )
        elif pattern_type == "session_hijacking":
            return self._generate_session_hijacking(
                victim_count, attacker_count, actual_start_date, end_date
            )
        elif pattern_type == "sim_swap":
            return self._generate_sim_swap(
                victim_count, attacker_count, actual_start_date, end_date
            )
        elif pattern_type == "phishing_campaign":
            return self._generate_phishing_campaign(
                victim_count, attacker_count, actual_start_date, end_date
            )
        elif pattern_type == "malware_based":
            return self._generate_malware_based(
                victim_count, attacker_count, actual_start_date, end_date
            )
        else:
            raise ValueError(f"Unknown CATO pattern type: {pattern_type}")
    
    def _generate_credential_stuffing(
        self,
        victim_count: int,
        attacker_count: int,
        start_date: datetime,
        end_date: datetime
    ) -> Pattern:
        """Generate credential stuffing attack pattern."""
        victims = [self.person_gen.generate() for _ in range(victim_count)]
        attackers = [self.person_gen.generate() for _ in range(attacker_count)]
        
        victim_accounts = [
            self.account_gen.generate(owner_id=victim.person_id, owner_type="person")
            for victim in victims
        ]
        
        # Attacker infrastructure
        attacker_ips = [self._generate_ip_address() for _ in range(attacker_count * 3)]
        attacker_devices = [f"Bot-{i:04d}" for i in range(attacker_count * 5)]
        
        transactions: List[Transaction] = []
        communications: List[Communication] = []
        indicators: List[str] = []
        red_flags: List[str] = []
        
        # Phase 1: Reconnaissance (phishing emails)
        recon_date = start_date
        for victim in victims:
            comm = self.communication_gen.generate()
            # Override generated values with our pattern data
            comm.sender_id = attackers[0].person_id
            comm.receiver_id = victim.person_id
            comm.timestamp = recon_date
            communications.append(comm)
        
        indicators.append("Phishing emails sent to all victims")
        red_flags.append("Coordinated phishing campaign detected")
        
        # Phase 2: Credential testing (multiple failed logins)
        testing_date = start_date + timedelta(hours=24)
        failed_attempts = 0
        
        for account in victim_accounts:
            # 5-15 failed login attempts per account
            attempts = random.randint(5, 15)
            failed_attempts += attempts
            
            for _ in range(attempts):
                indicators.append(
                    f"Failed login attempt on {account.account_number} from {random.choice(attacker_ips)}"
                )
        
        if failed_attempts > 50:
            red_flags.append(f"High volume of failed logins: {failed_attempts} attempts")
        
        # Phase 3: Successful takeover
        takeover_date = testing_date + timedelta(hours=2)
        total_stolen = Decimal("0")
        
        for account in victim_accounts:
            # Successful login from attacker IP
            attacker_ip = random.choice(attacker_ips)
            attacker_device = random.choice(attacker_devices)
            
            indicators.append(
                f"Successful login to {account.account_number} from {attacker_ip} (device: {attacker_device})"
            )
            red_flags.append(f"Login from new device/location for {account.account_number}")
            
            # Rapid account changes
            indicators.append(f"Email changed for {account.account_number}")
            indicators.append(f"Phone number changed for {account.account_number}")
            red_flags.append("Multiple account changes within minutes of login")
            
            # Fraudulent transactions
            for _ in range(random.randint(2, 5)):
                amount = random_amount(1000, 5000)
                total_stolen += amount
                
                txn = self.transaction_gen.generate(
                    from_account_id=account.account_id,
                    to_account_id=self.account_gen.generate().account_id
                )
                # Override generated values
                txn.amount = amount
                txn.timestamp = takeover_date + timedelta(minutes=random.randint(5, 30))
                transactions.append(txn)
        
        indicators.append(f"Total amount stolen: ${total_stolen:,.2f}")
        red_flags.append(f"Large-scale coordinated theft: ${total_stolen:,.2f}")
        
        # Calculate confidence and severity
        confidence_score = self._calculate_confidence_score(
            len(indicators), len(red_flags), victim_count, failed_attempts
        )
        
        severity_score = self._calculate_severity_score(
            confidence_score, total_stolen, victim_count, len(indicators)
        )
        
        return Pattern(
            pattern_id=f"CATO-CS-{self._generate_id()}",
            pattern_type="account_takeover",
            detection_method="coordinated_account_takeover_detection",
            description=f"Credential stuffing attack targeting {victim_count} accounts",
            start_date=start_date,
            end_date=end_date,
            entities=victims + attackers,
            accounts=victim_accounts,
            transactions=transactions,
            communications=communications,
            indicators=indicators,
            red_flags=red_flags,
            confidence_score=confidence_score,
            severity_score=severity_score,
            risk_level=self._determine_risk_level(severity_score),
            metadata={
                "attack_type": "credential_stuffing",
                "victim_count": victim_count,
                "attacker_count": attacker_count,
                "failed_attempts": failed_attempts,
                "total_stolen": float(total_stolen),
                "attacker_ips": attacker_ips,
                "attacker_devices": attacker_devices
            }
        )
    
    def _generate_session_hijacking(
        self,
        victim_count: int,
        attacker_count: int,
        start_date: datetime,
        end_date: datetime
    ) -> Pattern:
        """Generate session hijacking pattern."""
        victims = [self.person_gen.generate() for _ in range(victim_count)]
        attackers = [self.person_gen.generate() for _ in range(attacker_count)]
        
        victim_accounts = [
            self.account_gen.generate(owner_id=victim.person_id, owner_type="person")
            for victim in victims
        ]
        
        transactions: List[Transaction] = []
        indicators: List[str] = []
        red_flags: List[str] = []
        
        total_stolen = Decimal("0")
        
        for account in victim_accounts:
            # Legitimate session start
            legitimate_ip = self._generate_ip_address()
            session_start = start_date + timedelta(hours=random.randint(0, 24))
            
            indicators.append(
                f"Legitimate session started for {account.account_number} from {legitimate_ip}"
            )
            
            # Session hijacking (IP change mid-session)
            hijack_time = session_start + timedelta(minutes=random.randint(5, 30))
            attacker_ip = self._generate_ip_address()
            
            indicators.append(
                f"Session IP changed from {legitimate_ip} to {attacker_ip} without re-authentication"
            )
            red_flags.append(f"Suspicious IP change mid-session for {account.account_number}")
            
            # Unusual activity post-hijack
            indicators.append(f"Rapid navigation pattern change detected")
            indicators.append(f"Typing speed anomaly detected")
            red_flags.append("Behavioral biometric deviation detected")
            
            # Fraudulent transactions
            for _ in range(random.randint(1, 3)):
                amount = random_amount(2000, 10000)
                total_stolen += amount
                
                txn = self.transaction_gen.generate(
                    from_account_id=account.account_id,
                    to_account_id=self.account_gen.generate().account_id
                )
                txn.amount = amount
                txn.timestamp = hijack_time + timedelta(minutes=random.randint(1, 15))
                transactions.append(txn)
        
        confidence_score = self._calculate_confidence_score(
            len(indicators), len(red_flags), victim_count, 0
        )
        
        severity_score = self._calculate_severity_score(
            confidence_score, total_stolen, victim_count, len(indicators)
        )
        
        return Pattern(
            pattern_id=f"CATO-SH-{self._generate_id()}",
            pattern_type="account_takeover",
            detection_method="session_hijacking_detection",
            description=f"Session hijacking attack on {victim_count} accounts",
            start_date=start_date,
            end_date=end_date,
            entities=victims + attackers,
            accounts=victim_accounts,
            transactions=transactions,
            communications=[],
            indicators=indicators,
            red_flags=red_flags,
            confidence_score=confidence_score,
            severity_score=severity_score,
            risk_level=self._determine_risk_level(severity_score),
            metadata={
                "attack_type": "session_hijacking",
                "victim_count": victim_count,
                "total_stolen": float(total_stolen)
            }
        )
    
    def _generate_sim_swap(
        self,
        victim_count: int,
        attacker_count: int,
        start_date: datetime,
        end_date: datetime
    ) -> Pattern:
        """Generate SIM swap attack pattern."""
        victims = [self.person_gen.generate() for _ in range(victim_count)]
        attackers = [self.person_gen.generate() for _ in range(attacker_count)]
        
        victim_accounts = [
            self.account_gen.generate(owner_id=victim.person_id, owner_type="person")
            for victim in victims
        ]
        
        transactions: List[Transaction] = []
        communications: List[Communication] = []
        indicators: List[str] = []
        red_flags: List[str] = []
        
        total_stolen = Decimal("0")
        
        for i, account in enumerate(victim_accounts):
            victim = victims[i]
            attacker = attackers[i % attacker_count]
            
            # Phase 1: Social engineering call to carrier
            call_date = start_date + timedelta(hours=random.randint(0, 12))
            comm = self.communication_gen.generate()
            comm.sender_id = attacker.person_id
            comm.receiver_id = victim.person_id
            comm.timestamp = call_date
            communications.append(comm)
            
            indicators.append(f"Phone carrier contacted for {victim.name}")
            
            # Phase 2: SIM swap executed
            swap_date = call_date + timedelta(hours=1)
            indicators.append(f"SIM card swapped for {victim.phone}")
            red_flags.append(f"Unauthorized SIM swap detected for {victim.phone}")
            
            # Phase 3: SMS 2FA codes intercepted
            indicators.append(f"2FA codes redirected to new SIM")
            red_flags.append("Multiple 2FA bypass attempts detected")
            
            # Phase 4: Account takeover
            takeover_date = swap_date + timedelta(minutes=30)
            indicators.append(f"Account {account.account_number} accessed with 2FA codes")
            
            # Fraudulent transactions
            for _ in range(random.randint(2, 4)):
                amount = random_amount(3000, 15000)
                total_stolen += amount
                
                txn = self.transaction_gen.generate(
                    from_account_id=account.account_id,
                    to_account_id=self.account_gen.generate().account_id
                )
                txn.amount = amount
                txn.timestamp = takeover_date + timedelta(minutes=random.randint(5, 20))
                transactions.append(txn)
        
        confidence_score = self._calculate_confidence_score(
            len(indicators), len(red_flags), victim_count, 0
        )
        
        severity_score = self._calculate_severity_score(
            confidence_score, total_stolen, victim_count, len(indicators)
        )
        
        return Pattern(
            pattern_id=f"CATO-SS-{self._generate_id()}",
            pattern_type="account_takeover",
            detection_method="sim_swap_detection",
            description=f"SIM swap attack targeting {victim_count} victims",
            start_date=start_date,
            end_date=end_date,
            entities=victims + attackers,
            accounts=victim_accounts,
            transactions=transactions,
            communications=communications,
            indicators=indicators,
            red_flags=red_flags,
            confidence_score=confidence_score,
            severity_score=severity_score,
            risk_level=self._determine_risk_level(severity_score),
            metadata={
                "attack_type": "sim_swap",
                "victim_count": victim_count,
                "total_stolen": float(total_stolen)
            }
        )
    
    def _generate_phishing_campaign(
        self,
        victim_count: int,
        attacker_count: int,
        start_date: datetime,
        end_date: datetime
    ) -> Pattern:
        """Generate coordinated phishing campaign pattern."""
        victims = [self.person_gen.generate() for _ in range(victim_count)]
        attackers = [self.person_gen.generate() for _ in range(attacker_count)]
        
        victim_accounts = [
            self.account_gen.generate(owner_id=victim.person_id, owner_type="person")
            for victim in victims
        ]
        
        transactions: List[Transaction] = []
        communications: List[Communication] = []
        indicators: List[str] = []
        red_flags: List[str] = []
        
        # Phase 1: Mass phishing emails
        campaign_start = start_date
        for victim in victims:
            comm = self.communication_gen.generate()
            comm.sender_id = attackers[0].person_id
            comm.receiver_id = victim.person_id
            comm.timestamp = campaign_start
            communications.append(comm)
        
        indicators.append(f"Phishing emails sent to {victim_count} targets")
        red_flags.append("Large-scale phishing campaign detected")
        
        # Phase 2: Credential harvesting (30% success rate)
        compromised_count = int(victim_count * 0.3)
        compromised_accounts = random.sample(victim_accounts, compromised_count)
        
        indicators.append(f"{compromised_count} victims clicked phishing links")
        red_flags.append(f"{compromised_count} credentials potentially compromised")
        
        # Phase 3: Account exploitation
        exploit_date = campaign_start + timedelta(hours=48)
        total_stolen = Decimal("0")
        
        for account in compromised_accounts:
            # Fraudulent transactions
            for _ in range(random.randint(1, 3)):
                amount = random_amount(1000, 8000)
                total_stolen += amount
                
                txn = self.transaction_gen.generate(
                    from_account_id=account.account_id,
                    to_account_id=self.account_gen.generate().account_id
                )
                txn.amount = amount
                txn.timestamp = exploit_date + timedelta(hours=random.randint(0, 24))
                transactions.append(txn)
        
        confidence_score = self._calculate_confidence_score(
            len(indicators), len(red_flags), victim_count, 0
        )
        
        severity_score = self._calculate_severity_score(
            confidence_score, total_stolen, compromised_count, len(indicators)
        )
        
        return Pattern(
            pattern_id=f"CATO-PC-{self._generate_id()}",
            pattern_type="account_takeover",
            detection_method="phishing_campaign_detection",
            description=f"Phishing campaign targeting {victim_count} individuals",
            start_date=start_date,
            end_date=end_date,
            entities=victims + attackers,
            accounts=victim_accounts,
            transactions=transactions,
            communications=communications,
            indicators=indicators,
            red_flags=red_flags,
            confidence_score=confidence_score,
            severity_score=severity_score,
            risk_level=self._determine_risk_level(severity_score),
            metadata={
                "attack_type": "phishing_campaign",
                "victim_count": victim_count,
                "compromised_count": compromised_count,
                "total_stolen": float(total_stolen)
            }
        )
    
    def _generate_malware_based(
        self,
        victim_count: int,
        attacker_count: int,
        start_date: datetime,
        end_date: datetime
    ) -> Pattern:
        """Generate malware-based account takeover pattern."""
        victims = [self.person_gen.generate() for _ in range(victim_count)]
        attackers = [self.person_gen.generate() for _ in range(attacker_count)]
        
        victim_accounts = [
            self.account_gen.generate(owner_id=victim.person_id, owner_type="person")
            for victim in victims
        ]
        
        transactions: List[Transaction] = []
        indicators: List[str] = []
        red_flags: List[str] = []
        
        # Malware infection indicators
        indicators.append(f"Malware detected on {victim_count} devices")
        indicators.append("Keylogger activity detected")
        indicators.append("Screen capture malware identified")
        red_flags.append("Banking trojan detected")
        
        # Credential theft
        total_stolen = Decimal("0")
        
        for account in victim_accounts:
            indicators.append(f"Credentials stolen for {account.account_number}")
            
            # Delayed exploitation (malware waits to avoid detection)
            exploit_date = start_date + timedelta(days=random.randint(3, 7))
            
            # Fraudulent transactions
            for _ in range(random.randint(2, 5)):
                amount = random_amount(2000, 12000)
                total_stolen += amount
                
                txn = self.transaction_gen.generate(
                    from_account_id=account.account_id,
                    to_account_id=self.account_gen.generate().account_id
                )
                txn.amount = amount
                txn.timestamp = exploit_date + timedelta(hours=random.randint(0, 48))
                transactions.append(txn)
        
        red_flags.append(f"Coordinated malware-based theft: ${total_stolen:,.2f}")
        
        confidence_score = self._calculate_confidence_score(
            len(indicators), len(red_flags), victim_count, 0
        )
        
        severity_score = self._calculate_severity_score(
            confidence_score, total_stolen, victim_count, len(indicators)
        )
        
        return Pattern(
            pattern_id=f"CATO-MB-{self._generate_id()}",
            pattern_type="account_takeover",
            detection_method="malware_based_detection",
            description=f"Malware-based account takeover affecting {victim_count} accounts",
            start_date=start_date,
            end_date=end_date,
            entities=victims + attackers,
            accounts=victim_accounts,
            transactions=transactions,
            communications=[],
            indicators=indicators,
            red_flags=red_flags,
            confidence_score=confidence_score,
            severity_score=severity_score,
            risk_level=self._determine_risk_level(severity_score),
            metadata={
                "attack_type": "malware_based",
                "victim_count": victim_count,
                "total_stolen": float(total_stolen),
                "malware_type": "banking_trojan"
            }
        )
    
    def _calculate_confidence_score(
        self,
        indicator_count: int,
        red_flag_count: int,
        victim_count: int,
        failed_attempts: int
    ) -> float:
        """Calculate pattern confidence score (0-1)."""
        score = 0.0
        
        # Indicator weight
        if indicator_count >= 20:
            score += 0.3
        elif indicator_count >= 10:
            score += 0.2
        else:
            score += 0.1
        
        # Red flag weight
        if red_flag_count >= 10:
            score += 0.3
        elif red_flag_count >= 5:
            score += 0.2
        else:
            score += 0.1
        
        # Victim count weight
        if victim_count >= 10:
            score += 0.2
        elif victim_count >= 5:
            score += 0.15
        else:
            score += 0.1
        
        # Failed attempts weight (for credential stuffing)
        if failed_attempts > 100:
            score += 0.2
        elif failed_attempts > 50:
            score += 0.15
        elif failed_attempts > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_severity_score(
        self,
        confidence_score: float,
        total_value: Decimal,
        victim_count: int,
        indicator_count: int
    ) -> float:
        """Calculate pattern severity score (0-1)."""
        score = confidence_score * 0.4
        
        # Financial impact
        if total_value > Decimal("100000"):
            score += 0.3
        elif total_value > Decimal("50000"):
            score += 0.2
        else:
            score += 0.1
        
        # Scale of attack
        if victim_count >= 10:
            score += 0.2
        elif victim_count >= 5:
            score += 0.15
        else:
            score += 0.1
        
        # Sophistication
        if indicator_count >= 20:
            score += 0.1
        
        return min(score, 1.0)
    
    def _determine_risk_level(self, severity_score: float) -> RiskLevel:
        """Determine risk level from severity score."""
        if severity_score >= 0.8:
            return RiskLevel.CRITICAL
        elif severity_score >= 0.6:
            return RiskLevel.HIGH
        elif severity_score >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_id(self) -> str:
        """Generate unique pattern ID."""
        return f"{random.randint(100000, 999999)}"

