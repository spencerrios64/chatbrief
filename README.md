# chatbrief

Turn old AI chats into a short context pack you can paste into any AI to carry on where
you left off.

**Use it here: https://spencerrios64.github.io/chatbrief/**

It is a single web page (`index.html`) with no dependencies and no server. Your files are
read in your browser and never uploaded. Works on desktop and on Android.

## Use

1. In each AI's settings, request a data export and download the file it sends you.
2. Open the page, pick the export files, and tick the chats that belong to one project.
3. Choose a size, then **Copy** the pack and paste it as the first message of a new chat.

For each chat the pack holds: how it started, your preferences and instructions, the
decisions you made, things that may still be open, and where it left off.

## What it can and can't do

- It does not use an AI. It keeps sentences from **your own messages** that match phrases
  such as "I want", "always", "let's go with" or "still need to". That keeps it private and
  free, but it can miss things or keep the wrong sentence. Read the pack before relying on it.
- The phrase rules are English. Chats in other languages still get the start and the
  "where it left off" parts.
- The pack can contain anything you typed, including keys or personal details. Run the
  export through [chatscrub](https://github.com/spencerrios64/chatscrub) first if you plan to share it.
- It reads export files. It cannot log in to your accounts or fetch chats by itself.
- **Claude** and **ChatGPT** exports are tested on small sample exports. **Gemini**, **Grok** and
  **DeepSeek** are read from their documented formats and have not been checked against real exports.
- Exports over 4 GB (zip64) aren't supported: unzip them and pick the `.json` inside.

## Claude plugin

This repo is also a Claude plugin marketplace, so Claude can do the same job in a chat. In Claude Code:

```
/plugin marketplace add spencerrios64/chatbrief
/plugin install chatbrief@chatbrief
```

In the Claude app, download the `plugin` folder as a zip, rename it to `.plugin` and open it in a chat. Details: [plugin/README.md](plugin/README.md).

Part of a family of small tools for AI chats: [chatvault](https://github.com/spencerrios64/chatvault), [chatzip](https://github.com/spencerrios64/chatzip), [chatrelay](https://github.com/spencerrios64/chatrelay), [chatbrief](https://github.com/spencerrios64/chatbrief), [chatscrub](https://github.com/spencerrios64/chatscrub), [chatcompare](https://github.com/spencerrios64/chatcompare), [chatstats](https://github.com/spencerrios64/chatstats) and [promptbank](https://github.com/spencerrios64/promptbank).
# chatbrief

Turn old AI chats into a short context pack you can paste into any AI to carry on where
you left off.

**Use it here: https://spencerrios64.github.io/chatbrief/**

It is a single web page (`index.html`) with no dependencies and no server. Your files are
read in your browser and never uploaded. Works on desktop and on Android.

## Use

1. In each AI's settings, request a data export and download the file it sends you.
2. Open the page, pick the export files, and tick the chats that belong to one project.
3. Choose a size, then **Copy** the pack and paste it as the first message of a new chat.

For each chat the pack holds: how it started, your preferences and instructions, the
decisions you made, things that may still be open, and where it left off.

## What it can and can't do

- It does not use an AI. It keeps sentences from **your own messages** that match phrases
  such as "I want", "always", "let's go with" or "still need to". That keeps it private and
  free, but it can miss things or keep the wrong sentence. Read the pack before relying on it.
- The phrase rules are English. Chats in other languages still get the start and the
  "where it left off" parts.
- The pack can contain anything you typed, including keys or personal details. Run the
  export through [chatscrub](https://github.com/spencerrios64/chatscrub) first if you plan to share it.
- It reads export files. It cannot log in to your accounts or fetch chats by itself.
- **Claude** and **ChatGPT** exports are tested on small sample exports. **Gemini**, **Grok** and
  **DeepSeek** are read from their documented formats and have not been checked against real exports.
- Exports over 4 GB (zip64) aren't supported: unzip them and pick the `.json` inside.

Part of a family of small tools for AI chats: [chatvault](https://github.com/spencerrios64/chatvault), [chatzip](https://github.com/spencerrios64/chatzip), [chatrelay](https://github.com/spencerrios64/chatrelay), [chatbrief](https://github.com/spencerrios64/chatbrief), [chatscrub](https://github.com/spencerrios64/chatscrub), [chatcompare](https://github.com/spencerrios64/chatcompare), [chatstats](https://github.com/spencerrios64/chatstats) and [promptbank](https://github.com/spencerrios64/promptbank).
