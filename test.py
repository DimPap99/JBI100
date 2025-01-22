import pandas as pd

# Load the CSV file
file_path = 'shark.csv'  # Replace with the path to your CSV file
data = pd.read_csv(file_path)

# Calculate the total number of non-null values for each column
non_null_counts = data.notnull().sum()

# Convert the result to a DataFrame for better readability
non_null_counts_df = non_null_counts.reset_index()
non_null_counts_df.columns = ['Column', 'Non-Null Values']

# Display the result
print(non_null_counts_df)

###########################################

# print(data["Site.category"].unique())

# # Custom Mapping for each category
# custom_mapping = {
#     'coastal': 1,
#     'estuary/harbour': 2,
#     'island open ocean': 3,
#     'river': 4,
#     'ocean/pelagic': 5,
#     'fish farm': 6
# }

# data['Site.category.mapped'] = data['Site.category'].map(custom_mapping)
# print(data["Site.category.mapped"])

########################################################

def categorical_to_numerical(field_name, data):
    custom_mapping = {}
    unique_categories = data[field_name].unique()
    # dynamic custom mapping
    for idx, category in enumerate(unique_categories):
        custom_mapping[category] = idx + 1
    # new column's name
    mapped_column = field_name + '.mapped'
    mapped_column = str(mapped_column)
    data[mapped_column] = data[field_name].map(custom_mapping)
    return data


def non_null(column1, column2, column3, data):
    shared_count = data[column1].notnull() & data[column2].notnull() & data[column3].notnull()
    return shared_count.sum()

## Site.category cleaning
data["Site.category"] = data["Site.category"]. replace(['Coastal','Ocean/pelagic', 'other: fish farm'],
                                                       ['coastal','ocean/pelagic', 'fish farm'] )

# adding column with mapped site.category
data = categorical_to_numerical('Site.category', data)

## Injury.severity
data["Injury.severity"] = data["Injury.severity"]. replace(['other: teeth marks', 'fatality'],
                                                       ['teeth marks','fatal'] )

data = categorical_to_numerical('Injury.severity', data)
print(data)

print("############################################")

column1 = "Site.category"
column2 = "Distance.to.shore.m"
column3 = "Injury.severity"
column4 = 'Shark.length.m'


# unique_categories = data["Shark.identification.method"]
# print(unique_categories)

################ CHECK FOR NULL VALUES ###########################

shared_nulls = data[pd.isnull(data[column2]) & pd.isnull(data[column4])]
print(f'Shared null values are{shared_nulls}')