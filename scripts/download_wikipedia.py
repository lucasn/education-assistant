import wikipedia

# Get article text
text = wikipedia.page("Respiratory system").content

# Save to file
with open("file4-respiratory.txt", "w", encoding="utf-8") as file:
    file.write(text)

print("Article saved")