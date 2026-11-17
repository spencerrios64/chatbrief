# chatbrief plugin

Turn old AI chats into a short context pack to paste into any AI, with your preferences, decisions and open items.

## What you can ask

- "Make a context pack from my old chats about my Godot game" (attach your exports)
- "Brief ChatGPT on everything we decided in these chats"
- "Carry this project over to a new chat"

## What it can't do

It spots phrases in **your own messages** ("I want", "always", "let's go with", "still need to"); it does not understand the chats. Claude reads the result and fixes what it can confirm, but check the pack before relying on it. It works from the export files you give it and cannot log in to your accounts.

Project: https://github.com/spencerrios64/chatbrief

## Install

In Claude Code:

```
/plugin marketplace add spencerrios64/chatbrief
/plugin install chatbrief@chatbrief
```

In the Claude app, download the `plugin` folder as a zip, rename it to `.plugin` and open it in a chat.
