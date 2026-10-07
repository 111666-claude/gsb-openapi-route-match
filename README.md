# openapi-route-match

把请求匹配到路由：方法集合、主机通配、路径模板（静态/参数/末尾通配）、逐段优先级，以及重复注册的覆盖。只用 Python 标准库。

```
python3 -m unittest discover -s tests
python3 -m routematch --sample=priority
python3 -m routematch --sample=host
python3 -m routematch --sample=decode
python3 -m routematch --sample=methods
python3 -m routematch --sample=overlay
python3 -m routematch --sample=work
```

## 口径

- **分段**：路径先按 `/` 分段、丢掉空段，再对每段单独做百分号解码（`%2F` 不会变成新的分段）。
- **方法**：路由用 `methods` 列表（或单个 `method`）声明；请求方法要在里面。
- **主机**：路由主机可以是精确值、`*.后缀`（匹配任意子域）或 `*`（匹配任意主机）；不写表示不限制。
- **路径**：`{name}` 匹配恰好一段；`{name...}` 匹配一段或多段且必须是模板最后一段；其它段按字面比较。
- **优先**：逐段从左到右比较，字面段优先于参数段、参数段优先于通配段，第一个不同的段就决定胜负；完全并列时取路由表顺序。
- **覆盖**：方法集合与路径模板都相同的路由重复注册时，后者覆盖前者。
- **查找**：按方法集合与首段字面建索引，不逐条比较。

## 不变量

- 返回的路由方法一定包含请求方法，段数也一致。
- 被选中的路由按逐段优先级不劣于任何其它命中路由。
- `scanned` 不随路由数乘请求数放大：八百对八百的 `scanned` 不超过 6000。

## 输出契约

`match(method, host, path)` 返回命中的路由名或空串。场景打印一行 JSON。
`--sample=work` 打印 `{"routes": N, "scanned": N}`。
