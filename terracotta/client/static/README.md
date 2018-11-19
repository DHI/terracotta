# Terracotta client

## Developer notes

You don't need to install or run anything to use the clients.
Should you want to tweak the code, it might come in handy to run the commands listed below.

That said, you need to have the following first:
- node v8 +
- npx: `npm install -g npx`

## Running type checks

Static type checks are done with TypeScript.
Types are written using JSDoc. You can find a quick intro on it [here](https://github.com/Microsoft/TypeScript/wiki/JSDoc-support-in-JavaScript).

To do a typecheck, run:

```bash
$ npx typescript ./map.js --allowJs --noEmit --checkJs --target ES2017
```

For development, you might find it handy to have tsc run automatically:

```bash
$ npx typescript ./map.js --allowJs --noEmit --checkJs --target ES2017 --watch
```
