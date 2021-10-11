# article-rec-db

This repository stores the article rec db migrations that are controlled via flyway.


## Installing Dependencies
```
brew update && brew bundle
```

## Connecting to the DB
**Start Interactive PostgreSQL Session**

```
kar connect dev
```

## Applying Migrations

```
kar flyway <stage> <cmd>
```

**List Migrations**

```
kar flyway dev info
```

**Run Migrations**

```
kar flyway dev migrate
```
