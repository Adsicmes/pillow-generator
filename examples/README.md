# Examples

当前保留的示例都能在现有仓库结构下直接运行：

- `example_usage.py`：展示生成后的 Pillow 代码如何被调用
- `image_return_example.py`：展示返回 `PIL.Image.Image` 对象的用法
- `base_image_parameter_example.py`：展示底图作为参数传入时的写法，并会自动生成演示底图

运行前请先安装项目依赖，然后在仓库根目录执行：

```bash
python examples/example_usage.py
python examples/image_return_example.py
python examples/base_image_parameter_example.py
```

生成结果默认会写入 `examples/output/`。
