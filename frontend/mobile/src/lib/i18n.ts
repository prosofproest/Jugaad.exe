import type { Language } from "./workspace/types";

export type NavKey =
  | "nav.dashboard"
  | "nav.farms"
  | "nav.scan"
  | "nav.analysis"
  | "nav.assistant"
  | "nav.farmMap"
  | "nav.hotspots"
  | "nav.monitoring"
  | "nav.expert"
  | "nav.notifications"
  | "nav.help"
  | "nav.profile"
  | "nav.settings"
  | "nav.more"
  | "action.signOut"
  | "action.addFarm"
  | "action.scanPlant"
  | "common.offline"
  | "common.syncNow"
  | "common.demo";

type Catalogue = Record<NavKey, string>;

const en: Catalogue = {
  "nav.dashboard": "Dashboard",
  "nav.farms": "Farms",
  "nav.scan": "Scan",
  "nav.analysis": "AI analysis",
  "nav.assistant": "Assistant",
  "nav.farmMap": "Farm health map",
  "nav.hotspots": "Pest hotspots",
  "nav.monitoring": "Monitoring",
  "nav.expert": "Expert desk",
  "nav.notifications": "Notifications",
  "nav.help": "Help & support",
  "nav.profile": "Profile",
  "nav.settings": "Settings",
  "nav.more": "More",
  "action.signOut": "Switch account",
  "action.addFarm": "Add farm",
  "action.scanPlant": "Scan a plant",
  "common.offline": "Offline queue",
  "common.syncNow": "Sync now",
  "common.demo": "Demo data",
};

const hi: Catalogue = {
  ...en,
  "nav.dashboard": "डैशबोर्ड",
  "nav.farms": "खेत",
  "nav.scan": "स्कैन",
  "nav.analysis": "एआई विश्लेषण",
  "nav.assistant": "सहायक",
  "nav.farmMap": "खेत स्वास्थ्य नक्शा",
  "nav.hotspots": "कीट हॉटस्पॉट",
  "nav.monitoring": "निगरानी",
  "nav.expert": "विशेषज्ञ डेस्क",
  "nav.notifications": "सूचनाएं",
  "nav.help": "सहायता",
  "nav.profile": "प्रोफ़ाइल",
  "nav.settings": "सेटिंग्स",
  "nav.more": "अधिक",
  "action.signOut": "खाता बदलें",
  "action.addFarm": "खेत जोड़ें",
  "action.scanPlant": "पौधा स्कैन करें",
  "common.offline": "ऑफ़लाइन कतार",
  "common.syncNow": "अभी सिंक करें",
};

const kn: Catalogue = {
  ...en,
  "nav.dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
  "nav.farms": "ತೋಟಗಳು",
  "nav.scan": "ಸ್ಕ್ಯಾನ್",
  "nav.analysis": "ಎಐ ವಿಶ್ಲೇಷಣೆ",
  "nav.assistant": "ಸಹಾಯಕ",
  "nav.farmMap": "ತೋಟ ಆರೋಗ್ಯ ನಕ್ಷೆ",
  "nav.hotspots": "ಕೀಟ ಹಾಟ್‌ಸ್ಪಾಟ್",
  "nav.monitoring": "ಮೇಲ್ವಿಚಾರಣೆ",
  "nav.expert": "ತಜ್ಞ ಡೆಸ್ಕ್",
  "nav.notifications": "ಅಧಿಸೂಚನೆಗಳು",
  "nav.help": "ಸಹಾಯ",
  "nav.profile": "ಪ್ರೊಫೈಲ್",
  "nav.settings": "ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
  "nav.more": "ಇನ್ನಷ್ಟು",
  "action.signOut": "ಖಾತೆ ಬದಲಿಸಿ",
  "action.addFarm": "ತೋಟ ಸೇರಿಸಿ",
  "action.scanPlant": "ಸಸ್ಯ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ",
  "common.offline": "ಆಫ್‌ಲೈನ್ ಸರದಿ",
  "common.syncNow": "ಈಗ ಸಿಂಕ್ ಮಾಡಿ",
};

const catalogues: Record<Language, Catalogue> = { en, hi, kn };

export function translate(language: Language, key: NavKey): string {
  return catalogues[language][key] ?? en[key];
}
