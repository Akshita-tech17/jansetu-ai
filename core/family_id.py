"""
core/family_id.py: UP Family ID (एक परिवार, एक पहचान) Database & Resolver.
Models the ~4 crore families linked under Uttar Pradesh's Family ID portal.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class FamilyMember(BaseModel):
    member_id: str
    name: str
    relation: str  # Head, Wife, Mother, Daughter, Son
    age: int
    gender: str
    occupation: str
    education: Optional[str] = None
    aadhaar_linked: bool = True
    disability_status: bool = False
    existing_benefits: List[str] = Field(default_factory=list)


class FamilyProfile(BaseModel):
    family_id: str  # 12-digit UP Family ID (e.g. 24018291024)
    head_name: str
    ration_card_number: str
    district: str
    block_or_ward: str
    village_or_mohalla: str
    residency_type: str  # rural / urban
    annual_income: float
    social_category: str  # SC, ST, OBC, General, Minority
    land_holding_acres: float
    housing_type: str  # Kutcha / Pucca
    primary_language: str  # Awadhi, Bhojpuri, Hindi, Urdu
    members: List[FamilyMember]


# Curated UP Household Database mirroring e-Kuber / Family ID records
FAMILY_DATABASE: Dict[str, FamilyProfile] = {
    "24018291024": FamilyProfile(
        family_id="24018291024",
        head_name="रामेश्वर प्रसाद",
        ration_card_number="218902194821",
        district="वाराणसी (Varanasi)",
        block_or_ward="पिंडरा (Pindra)",
        village_or_mohalla="मंगारी (Mangari)",
        residency_type="rural",
        annual_income=42000.0,
        social_category="OBC",
        land_holding_acres=1.1,
        housing_type="Kutcha",
        primary_language="Bhojpuri / Awadhi",
        members=[
            FamilyMember(
                member_id="M01",
                name="रामेश्वर प्रसाद",
                relation="Head (स्वयं)",
                age=62,
                gender="Male",
                occupation="लघु कृषक / बटाईदार",
                existing_benefits=["राशन कार्ड (पात्र गृहस्थी)"]
            ),
            FamilyMember(
                member_id="M02",
                name="प्रभावती देवी",
                relation="माता (Mother)",
                age=65,
                gender="Female",
                occupation="गृहणी",
                existing_benefits=[]
            ),
            FamilyMember(
                member_id="M03",
                name="अंजलि कुमारी",
                relation="पुत्री (Daughter)",
                age=14,
                gender="Female",
                occupation="छात्रा (कक्षा 9)",
                education="9th Standard",
                existing_benefits=[]
            ),
            FamilyMember(
                member_id="M04",
                name="राहुल कुमार",
                relation="पुत्र (Son)",
                age=19,
                gender="Male",
                occupation="आईटीआई छात्र (Electrician)",
                education="ITI 1st Year",
                existing_benefits=[]
            )
        ]
    ),
    "24089123441": FamilyProfile(
        family_id="24089123441",
        head_name="कल्लू अंसारी",
        ration_card_number="218904561234",
        district="प्रयागराज (Prayagraj)",
        block_or_ward="फूलपुर (Phulpur)",
        village_or_mohalla="बहादुरपुर (Bahadurpur)",
        residency_type="rural",
        annual_income=38000.0,
        social_category="Minority (OBC)",
        land_holding_acres=0.0,  # भूमिहीन बुनकर
        housing_type="Kutcha",
        primary_language="Urdu / Awadhi",
        members=[
            FamilyMember(
                member_id="M11",
                name="कल्लू अंसारी",
                relation="Head (स्वयं)",
                age=58,
                gender="Male",
                occupation="पारंपरिक बुनकर (Handloom Weaver)",
                existing_benefits=["राशन कार्ड"]
            ),
            FamilyMember(
                member_id="M12",
                name="शबाना खातून",
                relation="पत्नी (Wife)",
                age=52,
                gender="Female",
                occupation="गृहणी",
                existing_benefits=[]
            ),
            FamilyMember(
                member_id="M13",
                name="अरमान अंसारी",
                relation="पुत्र (Son)",
                age=20,
                gender="Male",
                occupation="पॉलिटेक्निक डिप्लोमा छात्र",
                education="Diploma Civil",
                existing_benefits=[]
            )
        ]
    )
}


def lookup_family(identifier: str) -> Optional[FamilyProfile]:
    """
    Resolves Family Profile by 12-digit UP Family ID, Ration Card, or citizen name.
    """
    clean_id = identifier.strip().replace(" ", "").replace("-", "")
    
    # Direct Family ID lookup
    if clean_id in FAMILY_DATABASE:
        return FAMILY_DATABASE[clean_id]

    # Ration card lookup
    for profile in FAMILY_DATABASE.values():
        if profile.ration_card_number == clean_id:
            return profile

    # Name match fallback
    for profile in FAMILY_DATABASE.values():
        if any(token in profile.head_name for token in identifier.split()):
            return profile

    # Default to Rameshwar Prasad profile for interactive hackathon demos if unindexed
    return FAMILY_DATABASE["24018291024"]

