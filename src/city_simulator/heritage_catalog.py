HeritageNameBank = dict[str, tuple[str, ...]]


HERITAGE_NAME_BANKS: dict[str, HeritageNameBank] = {
    "anglo": {
        "family": ("Jones", "Harcourt", "Korr", "Miller", "Bennett"),
        "adult": ("Dorothy", "Ron", "Jane", "John", "Anne", "Robert"),
        "child": ("Morty", "Emily", "Thomas", "Grace", "Henry", "Claire"),
    },
    "brazilian": {
        "family": ("Silva", "Santos", "Oliveira", "Pereira", "Costa"),
        "adult": ("Joao", "Mariana", "Lucas", "Camila", "Rafael", "Ana"),
        "child": ("Pedro", "Livia", "Mateus", "Clara", "Davi", "Sofia"),
    },
    "bulgarian": {
        "family": ("Ivanov", "Petrova", "Dimitrov", "Georgiev", "Nikolova"),
        "adult": ("Ivan", "Maria", "Georgi", "Elena", "Nikolay", "Viktoria"),
        "child": ("Dimitar", "Sofia", "Mila", "Boris", "Kalina", "Stefan"),
    },
    "cameroonian": {
        "family": ("Njoya", "Mbarga", "Tchoumi", "Mballa", "Kamga"),
        "adult": ("Samuel", "Amina", "Patrick", "Clarisse", "Jean", "Estelle"),
        "child": ("Joel", "Nadine", "Eric", "Mireille", "Yann", "Grace"),
    },
    "canadian": {
        "family": ("MacDonald", "Tremblay", "Wilson", "Campbell", "Gagnon"),
        "adult": ("Michael", "Marie", "David", "Claire", "Andrew", "Sophie"),
        "child": ("Liam", "Emma", "Noah", "Olivia", "Lucas", "Ava"),
    },
    "chinese": {
        "family": ("Li", "Wang", "Zhang", "Chen", "Liu"),
        "adult": ("Wei", "Mei", "Jun", "Lian", "Ming", "Xia"),
        "child": ("Tao", "Yan", "Hao", "Lin", "An", "Jia"),
    },
    "egyptian": {
        "family": ("Hassan", "Ibrahim", "Mahmoud", "Saleh", "Fahmy"),
        "adult": ("Ahmed", "Mona", "Karim", "Nour", "Omar", "Salma"),
        "child": ("Youssef", "Laila", "Mariam", "Ali", "Farida", "Ziad"),
    },
    "ethiopian": {
        "family": ("Tesfaye", "Bekele", "Alemu", "Gebre", "Mekonnen"),
        "adult": ("Dawit", "Mekdes", "Samuel", "Hana", "Yonas", "Selam"),
        "child": ("Abel", "Liya", "Nahom", "Mimi", "Kidus", "Rediet"),
    },
    "french": {
        "family": ("Martin", "Bernard", "Dubois", "Moreau", "Laurent"),
        "adult": ("Jean", "Claire", "Pierre", "Sophie", "Luc", "Camille"),
        "child": ("Louis", "Emma", "Hugo", "Lea", "Jules", "Manon"),
    },
    "guatemalan": {
        "family": ("Lopez", "Perez", "Gomez", "Castillo", "Morales"),
        "adult": ("Luis", "Maria", "Carlos", "Ana", "Jose", "Rosa"),
        "child": ("Diego", "Sofia", "Mateo", "Lucia", "Emilio", "Valeria"),
    },
    "haitian": {
        "family": ("Jean", "Pierre", "Joseph", "Charles", "Baptiste"),
        "adult": ("Jean", "Marie", "Frantz", "Nadia", "Emmanuel", "Mireille"),
        "child": ("Samuel", "Naomi", "Daniel", "Esther", "Marc", "Sabrina"),
    },
    "hispanic": {
        "family": ("Hernandez", "Garcia", "Martinez", "Lopez", "Rivera"),
        "adult": ("Juan", "Louise", "Carlos", "Marisol", "Elena", "Miguel"),
        "child": ("Renee", "Jose", "Sofia", "Diego", "Lucia", "Mateo"),
    },
    "israeli": {
        "family": ("Cohen", "Levi", "Mizrahi", "Biton", "Avraham"),
        "adult": ("Noam", "Yael", "Eitan", "Tamar", "Amit", "Shira"),
        "child": ("Ori", "Maya", "Itai", "Noga", "Lior", "Adi"),
    },
    "israeli_arab": {
        "family": ("Haddad", "Mansour", "Khoury", "Nassar", "Awad"),
        "adult": ("Samir", "Mariam", "Yousef", "Rana", "Khaled", "Lina"),
        "child": ("Omar", "Leila", "Adam", "Nour", "Amir", "Yasmin"),
    },
    "japanese": {
        "family": ("Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe"),
        "adult": ("Haruto", "Yui", "Ren", "Aoi", "Daiki", "Sakura"),
        "child": ("Sota", "Hina", "Yuto", "Mei", "Riku", "Mio"),
    },
    "jewish": {
        "family": ("Katan", "Cohen", "Levine", "Rosen", "Shapiro"),
        "adult": ("Yossi", "Miriam", "Ari", "Leah", "Noam", "Talia"),
        "child": ("Eli", "Naomi", "Avi", "Maya", "Dina", "Jonah"),
    },
    "korean": {
        "family": ("Kim", "Lee", "Park", "Choi", "Jung"),
        "adult": ("Minjun", "Jisoo", "Hyun", "Soojin", "Jiho", "Hana"),
        "child": ("Doyun", "Seoyeon", "Yuna", "Joon", "Minseo", "Eun"),
    },
    "mexican": {
        "family": ("Hernandez", "Garcia", "Martinez", "Rodriguez", "Sanchez"),
        "adult": ("Jose", "Guadalupe", "Miguel", "Carmen", "Alejandro", "Elena"),
        "child": ("Diego", "Valeria", "Santiago", "Sofia", "Emiliano", "Lucia"),
    },
    "nigerian": {
        "family": ("Okafor", "Adeyemi", "Balogun", "Eze", "Ibrahim"),
        "adult": ("Chinedu", "Amina", "Tunde", "Ngozi", "Emeka", "Zainab"),
        "child": ("Kelechi", "Aisha", "Ife", "Musa", "Ada", "Damilola"),
    },
    "polish": {
        "family": ("Nowak", "Kowalski", "Wisniewski", "Wojcik", "Kaminski"),
        "adult": ("Piotr", "Anna", "Marek", "Katarzyna", "Jan", "Ewa"),
        "child": ("Jakub", "Zofia", "Maja", "Adam", "Oliwia", "Filip"),
    },
    "portuguese": {
        "family": ("Silva", "Santos", "Ferreira", "Pereira", "Costa"),
        "adult": ("Joao", "Ana", "Miguel", "Ines", "Tiago", "Mariana"),
        "child": ("Tomas", "Leonor", "Duarte", "Matilde", "Afonso", "Beatriz"),
    },
    "romanian": {
        "family": ("Popescu", "Ionescu", "Dumitrescu", "Stan", "Radu"),
        "adult": ("Andrei", "Ioana", "Mihai", "Elena", "Vlad", "Ana"),
        "child": ("Matei", "Sofia", "Luca", "Maria", "Daria", "Alex"),
    },
    "russian": {
        "family": ("Ivanov", "Petrov", "Sokolov", "Volkov", "Smirnov"),
        "adult": ("Alexei", "Irina", "Dmitri", "Natalia", "Sergei", "Anya"),
        "child": ("Misha", "Sasha", "Nikita", "Katya", "Pavel", "Lena"),
    },
    "spanish": {
        "family": ("Garcia", "Fernandez", "Lopez", "Sanchez", "Martinez"),
        "adult": ("Antonio", "Maria", "Javier", "Laura", "Carlos", "Carmen"),
        "child": ("Hugo", "Lucia", "Mateo", "Sofia", "Pablo", "Valeria"),
    },
    "thai": {
        "family": ("Sukhum", "Wongchai", "Kittisak", "Rattanakul", "Chaiyaporn"),
        "adult": ("Somchai", "Malee", "Anan", "Nok", "Krit", "Siriporn"),
        "child": ("Arun", "Pim", "Niran", "Dao", "Tawan", "Mali"),
    },
    "ukrainian": {
        "family": ("Shevchenko", "Koval", "Bondarenko", "Tkachenko", "Kravchenko"),
        "adult": ("Oleksandr", "Olena", "Andriy", "Iryna", "Taras", "Nataliya"),
        "child": ("Bohdan", "Kateryna", "Danylo", "Sofia", "Maksym", "Oksana"),
    },
    "vietnamese": {
        "family": ("Nguyen", "Tran", "Le", "Pham", "Hoang"),
        "adult": ("Minh", "Lan", "Tuan", "Hoa", "Quang", "Mai"),
        "child": ("An", "Linh", "Bao", "Nhi", "Duc", "Thao"),
    },
}


HERITAGE_ALIASES: dict[str, str] = {
    "cameroon": "cameroonian",
    "camaroon": "cameroonian",
    "guatamalan": "guatemalan",
    "israeli arab": "israeli_arab",
    "israeli-arab": "israeli_arab",
}


HERITAGE_LANGUAGES: dict[str, tuple[str, ...]] = {
    "anglo": ("english",),
    "brazilian": ("portuguese",),
    "bulgarian": ("bulgarian",),
    "cameroonian": ("english", "french"),
    "canadian": ("english", "french"),
    "chinese": ("mandarin",),
    "egyptian": ("arabic",),
    "ethiopian": ("amharic",),
    "french": ("french",),
    "guatemalan": ("spanish",),
    "haitian": ("haitian_creole", "french"),
    "hispanic": ("english", "spanish"),
    "israeli": ("hebrew",),
    "israeli_arab": ("arabic", "hebrew"),
    "japanese": ("japanese",),
    "jewish": ("english", "hebrew"),
    "korean": ("korean",),
    "mexican": ("spanish",),
    "nigerian": ("english",),
    "polish": ("polish",),
    "portuguese": ("portuguese",),
    "romanian": ("romanian",),
    "russian": ("russian",),
    "spanish": ("spanish",),
    "thai": ("thai",),
    "ukrainian": ("ukrainian",),
    "vietnamese": ("vietnamese",),
}


def canonical_heritage(heritage: str) -> str:
    key = heritage.lower().replace("_", " ").strip()
    key = " ".join(key.split())
    return HERITAGE_ALIASES.get(key, key.replace(" ", "_"))


def heritage_names(heritage: str) -> HeritageNameBank:
    key = canonical_heritage(heritage)
    if key not in HERITAGE_NAME_BANKS:
        choices = ", ".join(sorted(HERITAGE_NAME_BANKS))
        raise ValueError(f"unknown heritage {heritage!r}; choose one of: {choices}")
    return HERITAGE_NAME_BANKS[key]


def heritage_languages(heritage: str) -> tuple[str, ...]:
    return HERITAGE_LANGUAGES.get(canonical_heritage(heritage), ("english",))
