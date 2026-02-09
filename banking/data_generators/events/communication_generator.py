"""
Communication Generator for Banking Compliance Use Cases

Generates realistic multi-modal communications (email, SMS, phone, chat, video, social media)
with multi-lingual content, sentiment analysis, and suspicious keyword injection for
insider trading, market manipulation, and fraud detection scenarios.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from faker import Faker

from ..core.base_generator import BaseGenerator
from ..utils.constants import COUNTRIES, LANGUAGES, SUSPICIOUS_KEYWORDS
from ..utils.data_models import Communication, CommunicationType
from ..utils.helpers import random_choice_weighted, random_datetime_between


class CommunicationGenerator(BaseGenerator[Communication]):
    """
    Generates realistic multi-modal communications with compliance indicators.

    Features:
    - Multi-modal: email, SMS, phone, chat, video, social media
    - Multi-lingual content generation (50+ languages)
    - Sentiment analysis scoring
    - Suspicious keyword injection
    - Attachment simulation
    - Platform-specific metadata
    - Thread/conversation tracking
    - Encryption status
    - Compliance flags

    Use Cases:
    - Insider trading detection (suspicious timing + keywords)
    - Market manipulation (coordinated messaging)
    - Fraud investigation (communication patterns)
    - Compliance monitoring (keyword scanning)
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize CommunicationGenerator.

        Args:
            seed: Random seed for reproducibility
            locale: Faker locale for content generation
            config: Additional configuration options
        """
        super().__init__(seed, locale, config)

        # Communication type distribution (realistic)
        self.type_weights = {
            CommunicationType.EMAIL: 0.35,  # 35% - most common in business
            CommunicationType.SMS: 0.20,  # 20% - mobile messaging
            CommunicationType.PHONE: 0.15,  # 15% - voice calls
            CommunicationType.CHAT: 0.15,  # 15% - instant messaging
            CommunicationType.VIDEO: 0.05,  # 5% - video calls
            CommunicationType.SOCIAL_MEDIA: 0.10,  # 10% - social platforms
        }

        # Sentiment distribution (realistic business communications)
        self.sentiment_weights = {
            "positive": 0.30,
            "neutral": 0.50,
            "negative": 0.15,
            "urgent": 0.05,
        }

        # Platform distribution by type
        self.platforms = {
            CommunicationType.EMAIL: ["Outlook", "Gmail", "Exchange", "ProtonMail"],
            CommunicationType.SMS: ["iMessage", "WhatsApp", "Signal", "Telegram"],
            CommunicationType.PHONE: ["Mobile", "Landline", "VoIP", "Skype"],
            CommunicationType.CHAT: ["Slack", "Teams", "Discord", "Jabber"],
            CommunicationType.VIDEO: ["Zoom", "Teams", "WebEx", "Google Meet"],
            CommunicationType.SOCIAL_MEDIA: ["LinkedIn", "Twitter", "Facebook", "WeChat"],
        }

        # Attachment types by communication type
        self.attachment_types = {
            CommunicationType.EMAIL: ["pdf", "docx", "xlsx", "pptx", "zip"],
            CommunicationType.SMS: ["jpg", "png", "mp4", "pdf"],
            CommunicationType.CHAT: ["jpg", "png", "gif", "pdf", "docx"],
            CommunicationType.SOCIAL_MEDIA: ["jpg", "png", "mp4", "gif"],
        }

        # Suspicious keyword categories for injection
        self.keyword_categories = list(SUSPICIOUS_KEYWORDS.keys())

        # Probability of suspicious content (configurable)
        self.suspicious_probability = config.get("suspicious_probability", 0.05) if config else 0.05

    def generate(
        self,
        sender_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        communication_type: Optional[CommunicationType] = None,
        language: Optional[str] = None,
        force_suspicious: bool = False,
    ) -> Communication:
        """
        Generate a single communication event.

        Args:
            sender_id: ID of sender (person or company)
            recipient_id: ID of recipient (person or company)
            communication_type: Type of communication (if None, randomly selected)
            language: Language code (if None, randomly selected)
            force_suspicious: Force inclusion of suspicious keywords

        Returns:
            Communication object with all attributes
        """
        # Generate IDs if not provided
        if not sender_id:
            sender_id = f"PER-{self.faker.uuid4()[:8]}"
        if not recipient_id:
            recipient_id = f"PER-{self.faker.uuid4()[:8]}"

        # Select communication type (ensure not None)
        if communication_type is None:
            communication_type = random_choice_weighted(list(self.type_weights.items()))

        # Select language (ensure not None)
        if language is None:
            lang_codes = list(LANGUAGES.keys())
            # 40% English, rest distributed equally
            lang_weights = [
                (code, 0.40 if code == "en" else 0.60 / (len(lang_codes) - 1))
                for code in lang_codes
            ]
            language = random_choice_weighted(lang_weights)

        # Generate timestamp (within last 90 days)
        timestamp = random_datetime_between(
            datetime.now(timezone.utc) - timedelta(days=90), datetime.now(timezone.utc)
        )

        # Generate content based on type and language
        subject, content = self._generate_content(
            communication_type,
            language,
            force_suspicious or random.random() < self.suspicious_probability,
        )

        # Select platform
        platform = random.choice(self.platforms[communication_type])

        # Generate sentiment
        sentiment = random_choice_weighted(list(self.sentiment_weights.items()))
        sentiment_score = self._calculate_sentiment_score(sentiment)

        # Generate metadata
        metadata = self._generate_metadata(communication_type, platform, language)

        # Generate attachments (30% probability)
        attachments = []
        if communication_type in self.attachment_types and random.random() < 0.30:
            attachments = self._generate_attachments(communication_type)

        # Detect suspicious keywords
        suspicious_keywords = self._detect_suspicious_keywords(subject, content)

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            communication_type, suspicious_keywords, sentiment, len(attachments), metadata
        )

        # Determine if encrypted (higher for sensitive platforms)
        is_encrypted = self._is_encrypted(platform, risk_score)

        # Generate thread ID (70% are part of threads)
        thread_id = None
        if random.random() < 0.70:
            thread_id = f"THREAD-{self.faker.uuid4()[:12]}"

        # Determine if flagged for review
        flagged_for_review = risk_score > 0.6 or len(suspicious_keywords) > 2

        return Communication(
            communication_id=f"COMM-{self.faker.uuid4()[:12]}",
            sender_id=sender_id,
            sender_type="person",  # Default to person, can be overridden
            recipient_ids=[recipient_id],  # Convert single ID to list
            recipient_types=["person"],  # Default to person
            communication_type=communication_type,
            timestamp=timestamp,
            subject=subject,
            content=content,
            language=language,
            platform=platform,
            sentiment_score=sentiment_score,
            suspicious_keywords=suspicious_keywords,
            has_attachments=len(attachments) > 0,
            attachment_count=len(attachments),
            attachment_types=[att["file_type"] for att in attachments],
            is_encrypted=is_encrypted,
            is_flagged=flagged_for_review,
            flag_reason="Suspicious keywords detected" if flagged_for_review else None,
            risk_score=risk_score,
            metadata=metadata,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def _generate_content(
        self, comm_type: CommunicationType, language: str, inject_suspicious: bool
    ) -> Tuple[Optional[str], str]:
        """
        Generate subject and content based on communication type and language.

        Args:
            comm_type: Type of communication
            language: Language code
            inject_suspicious: Whether to inject suspicious keywords

        Returns:
            Tuple of (subject, content)
        """
        # Get Faker instance for language (fallback to English)
        try:
            faker_lang = Faker(self._get_faker_locale(language))
        except:
            faker_lang = self.faker

        subject = None
        content = ""

        if comm_type == CommunicationType.EMAIL:
            subject = faker_lang.sentence(nb_words=6)
            content = "\n\n".join([faker_lang.paragraph(nb_sentences=3) for _ in range(2)])

        elif comm_type == CommunicationType.SMS:
            content = faker_lang.sentence(nb_words=random.randint(5, 15))

        elif comm_type == CommunicationType.PHONE:
            # Phone calls have transcripts
            content = f"Call duration: {random.randint(30, 1800)} seconds. "
            content += faker_lang.paragraph(nb_sentences=2)

        elif comm_type == CommunicationType.CHAT:
            content = faker_lang.sentence(nb_words=random.randint(3, 20))

        elif comm_type == CommunicationType.VIDEO:
            content = f"Video call duration: {random.randint(300, 3600)} seconds. "
            content += faker_lang.sentence(nb_words=10)

        elif comm_type == CommunicationType.SOCIAL_MEDIA:
            content = faker_lang.sentence(nb_words=random.randint(10, 30))

        # Inject suspicious keywords if required
        if inject_suspicious:
            category = random.choice(self.keyword_categories)
            keywords = random.sample(SUSPICIOUS_KEYWORDS[category], k=random.randint(1, 3))

            # Insert keywords naturally into content
            for keyword in keywords:
                if random.random() < 0.5 and subject:
                    subject = f"{subject} {keyword}"
                else:
                    content = f"{content} {keyword}"

        return subject, content

    def _get_faker_locale(self, language_code: str) -> str:
        """Map ISO 639-1 language code to Faker locale."""
        locale_map = {
            "en": "en_US",
            "es": "es_ES",
            "fr": "fr_FR",
            "de": "de_DE",
            "it": "it_IT",
            "pt": "pt_BR",
            "ru": "ru_RU",
            "zh": "zh_CN",
            "ja": "ja_JP",
            "ko": "ko_KR",
            "ar": "ar_SA",
            "hi": "hi_IN",
        }
        return locale_map.get(language_code, "en_US")

    def _calculate_sentiment_score(self, sentiment: str) -> float:
        """Calculate numerical sentiment score (-1 to 1)."""
        sentiment_scores = {
            "positive": random.uniform(0.5, 1.0),
            "neutral": random.uniform(-0.2, 0.2),
            "negative": random.uniform(-1.0, -0.5),
            "urgent": random.uniform(0.3, 0.8),
        }
        return sentiment_scores.get(sentiment, 0.0)

    def _generate_metadata(
        self, comm_type: CommunicationType, platform: str, language: str
    ) -> Dict[str, Any]:
        """Generate platform-specific metadata."""
        metadata: Dict[str, Any] = {
            "platform": platform,
            "language": language,
            "timezone": random.choice(list(COUNTRIES.values())[:20]),
        }

        if comm_type == CommunicationType.EMAIL:
            metadata.update(
                {
                    "from_address": self.faker.email(),
                    "to_address": self.faker.email(),
                    "cc_count": random.randint(0, 5),
                    "bcc_count": random.randint(0, 2),
                    "message_id": f"<{self.faker.uuid4()}@{self.faker.domain_name()}>",
                    "in_reply_to": (
                        f"<{self.faker.uuid4()}@{self.faker.domain_name()}>"
                        if random.random() < 0.4
                        else None
                    ),
                }
            )

        elif comm_type == CommunicationType.PHONE:
            metadata.update(
                {
                    "from_number": self.faker.phone_number(),
                    "to_number": self.faker.phone_number(),
                    "call_type": random.choice(["incoming", "outgoing", "missed"]),
                    "duration_seconds": random.randint(30, 1800),
                    "recording_available": random.random() < 0.3,
                }
            )

        elif comm_type == CommunicationType.SMS:
            metadata.update(
                {
                    "from_number": self.faker.phone_number(),
                    "to_number": self.faker.phone_number(),
                    "message_length": random.randint(10, 160),
                    "delivery_status": random.choice(["delivered", "sent", "failed"]),
                }
            )

        elif comm_type == CommunicationType.CHAT:
            metadata.update(
                {
                    "channel_id": f"CHAN-{self.faker.uuid4()[:8]}",
                    "workspace_id": f"WS-{self.faker.uuid4()[:8]}",
                    "message_type": random.choice(["text", "file", "mention", "reaction"]),
                }
            )

        elif comm_type == CommunicationType.VIDEO:
            metadata.update(
                {
                    "meeting_id": f"MTG-{self.faker.uuid4()[:12]}",
                    "duration_seconds": random.randint(300, 3600),
                    "participants_count": random.randint(2, 20),
                    "recording_available": random.random() < 0.5,
                    "screen_shared": random.random() < 0.4,
                }
            )

        elif comm_type == CommunicationType.SOCIAL_MEDIA:
            metadata.update(
                {
                    "post_id": f"POST-{self.faker.uuid4()[:12]}",
                    "likes_count": random.randint(0, 1000),
                    "shares_count": random.randint(0, 100),
                    "comments_count": random.randint(0, 50),
                    "visibility": random.choice(["public", "private", "connections"]),
                }
            )

        return metadata

    def _generate_attachments(self, comm_type: CommunicationType) -> List[Dict[str, Any]]:
        """Generate attachment metadata."""
        attachments = []
        num_attachments = random.randint(1, 3)

        for _ in range(num_attachments):
            file_type = random.choice(self.attachment_types[comm_type])
            file_size = random.randint(1024, 10485760)  # 1KB to 10MB

            attachments.append(
                {
                    "filename": f"{self.faker.word()}.{file_type}",
                    "file_type": file_type,
                    "file_size_bytes": file_size,
                    "checksum": self.faker.sha256(),
                }
            )

        return attachments

    def _detect_suspicious_keywords(self, subject: Optional[str], content: str) -> List[str]:
        """Detect suspicious keywords in content."""
        text = f"{subject or ''} {content}".lower()
        detected = []

        for category, keywords in SUSPICIOUS_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    detected.append(keyword)

        return list(set(detected))  # Remove duplicates

    def _calculate_risk_score(
        self,
        comm_type: CommunicationType,
        suspicious_keywords: List[str],
        sentiment: str,
        attachment_count: int,
        metadata: Dict[str, Any],
    ) -> float:
        """Calculate communication risk score (0-1)."""
        score = 0.0

        # Suspicious keywords (major factor)
        if len(suspicious_keywords) > 0:
            score += 0.3
        if len(suspicious_keywords) > 2:
            score += 0.2

        # Negative or urgent sentiment
        if sentiment in ["negative", "urgent"]:
            score += 0.1

        # Multiple attachments
        if attachment_count > 2:
            score += 0.1

        # Encrypted communications (slightly suspicious)
        if metadata.get("is_encrypted"):
            score += 0.05

        # Off-hours communication (suspicious timing)
        if "timestamp" in metadata:
            hour = metadata["timestamp"].hour
            if hour < 6 or hour > 22:
                score += 0.15

        # Social media with high engagement (potential market manipulation)
        if comm_type == CommunicationType.SOCIAL_MEDIA:
            if metadata.get("shares_count", 0) > 50:
                score += 0.1

        return min(score, 1.0)

    def _is_encrypted(self, platform: str, risk_score: float) -> bool:
        """Determine if communication is encrypted."""
        # Certain platforms always encrypt
        encrypted_platforms = ["Signal", "ProtonMail", "WhatsApp", "Telegram"]
        if platform in encrypted_platforms:
            return True

        # Higher risk communications more likely to be encrypted
        if risk_score > 0.5:
            return random.random() < 0.6

        return random.random() < 0.2

    def generate_conversation_thread(
        self,
        sender_id: str,
        recipient_id: str,
        message_count: int = 5,
        communication_type: Optional[CommunicationType] = None,
        time_window_hours: int = 24,
        suspicious_probability: float = 0.1,
    ) -> List[Communication]:
        """
        Generate a conversation thread between two parties.

        Args:
            sender_id: ID of primary sender
            recipient_id: ID of primary recipient
            message_count: Number of messages in thread
            communication_type: Type of communication (if None, randomly selected)
            time_window_hours: Time window for conversation
            suspicious_probability: Probability of suspicious content

        Returns:
            List of Communication objects forming a thread
        """
        thread_id = f"THREAD-{self.faker.uuid4()[:12]}"
        base_time = random_datetime_between(
            datetime.now(timezone.utc) - timedelta(days=30), datetime.now(timezone.utc)
        )

        # Select communication type for entire thread
        if not communication_type:
            communication_type = random_choice_weighted(list(self.type_weights.items()))

        communications = []
        current_sender = sender_id
        current_recipient = recipient_id

        for i in range(message_count):
            # Generate message
            comm = self.generate(
                sender_id=current_sender,
                recipient_id=current_recipient,
                communication_type=communication_type,
                force_suspicious=random.random() < suspicious_probability,
            )

            # Update timestamp to be within thread window
            offset_hours = (i / message_count) * time_window_hours
            comm.timestamp = base_time + timedelta(hours=offset_hours)
            comm.created_at = comm.timestamp
            comm.updated_at = comm.timestamp

            communications.append(comm)

            # Alternate sender/recipient for conversation flow
            current_sender, current_recipient = current_recipient, current_sender

        return communications
