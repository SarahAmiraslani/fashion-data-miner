def get_low_level(name: str, desc: str) -> str:

    parent_dir = str(Path(os.getcwd()).parent)
    ll_df = pd.read_csv(
        parent_dir
        + os.sep
        + "standardization-csvs"
        + os.sep
        + "LowLevelCatagoryRegex.csv",
        header=None,
        skiprows=[0],
    )

    # get all the low level categories regex patterns
    cats = []
    for _, row in ll_df.iloc[:, 1:].iterrows():
        cats.extend(row.dropna().tolist())

    # find the low level category regex that matches the input name (should match only one), get the corresponding low level category name
    for cat in cats:
        ll = "Other"
        if re.search(cat, name.lower()):
            ll = ll_df[(ll_df == cat).any(axis=1)].iloc[0, 0]
            break

        # if no re matches, try to use the description as a final try
        if ll == "Other":
            desc_words = [word.lower() for word in desc[0].split()]

            for word in desc_words:
                if re.search(cat, word):
                    ll = ll_df[(ll_df == cat).any(axis=1)].iloc[0, 0]

        # if ll is still other we need to update LowLevelCategoryRegex file
    return ll


def get_high_level(lower_level: str) -> str:
    parent_dir = str(Path(os.getcwd()).parent)
    hl_df = pd.read_csv(
        parent_dir
        + os.sep
        + "standardization-csvs"
        + os.sep
        + "HighLevelCatagory-LowLevelCatagory.csv"
    )

    return hl_df[(hl_df == lower_level.title()).any(axis=1)].iloc[0, 0]


def part_matching(raw_part: str) -> str:
    parent_dir = str(Path(os.getcwd()).parent)
    parts_df = pd.read_csv(
        parent_dir + os.sep + "standardization-csvs" + os.sep + "PartsRegex.csv"
    )

    # get all the parts regex patterns
    parts: list[str] = []
    for _, row in parts_df.iloc[:, 1:].iterrows():
        parts.extend(row[i] for i in parts_df.columns[1:] if not pd.isnull(row[i]))
    for part in parts:
        p = "All"
        if re.search(part, raw_part.strip().lower()):
            p = parts_df[(parts_df == part).any(axis=1)].iloc[0, 0]
            break

    return p


def materials_matching(raw_material: str):
    parent_dir = str(Path(os.getcwd()).parent)
    m_df = pd.read_csv(
        parent_dir + os.sep + "standardization-csvs" + os.sep + "MaterialProxy.csv"
    )

    # get all the materials regex patterns
    materials: list[str] = []
    for _, row in m_df.iloc[:, 1:].iterrows():
        materials.extend(row[i] for i in m_df.columns[1:] if not pd.isnull(row[i]))
    for material in materials:
        m = "other"
        if re.search(material, raw_material.strip().lower()):
            m = m_df[(m_df == material).any(axis=1)].iloc[0, 0]
            break

    return m
