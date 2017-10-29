# Data source for latubot

Provides REST API to update data. Updates fetched and parsed from softroi web
sites.

##

- `v1`
  - lists supported sports, `latu` or `luistelu`
- `v1/latu`
  - lists areas for sport, `OULU`, `SYOTE`, `SOTKAMOVUOKATTI`, etc. These can be accessed with case-insensitive names
- `v1/latu/oulu`
  - lists updates for cities and places within area. By default only cities and places with update data are listed - the empty places can be included in output with query parameter `all=true` Updates can be limited to only the most recent updates with query parameter `since=<timespan>`, where timespan must a number suffixed with `m`, `h`, `d` or `M` for minutes, hours, days, and months respectively. If no suffix is provided minutes are assumed. For example, `?since=4h` provides updates from the last 4 hours.

## TODO

API docs
