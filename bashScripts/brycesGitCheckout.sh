#!/bin/bash

# The filename is known and hardcoded
filename="git_checkout.list"

# Check if file exists and is readable
if [ ! -r "$filename" ]; then
    echo "File $filename not found or not readable"
    exit 1
fi

# Prompt for username and password
read -p "Username: " username
read -sp "Password: " password
echo

# Replace any '@' symbols in username with URL encoded value '%40'
username=${username//@/%40}


# Iterate over each URL in the file and clone the repository
while IFS= read -r url
do
    # Replace 'https://' with 'https://username:password@'
    url_with_credentials=${url/https:\/\//https:\/\/$username:$password@}
    git clone "$url_with_credentials"
done < "$filename"
