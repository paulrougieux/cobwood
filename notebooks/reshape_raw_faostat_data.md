---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.11.3
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

```python
# Load 
from cobwood.faostat import faostat
fo = faostat.read_csv("Forestry_E_All_Data_(Normalized).zip")
```

```python
fo
```

# Explore



## Column names

```python
fo.columns
```

## Area

```python
fo.area.unique()
```

## Item (product)

```python
fo.item.unique()
```

## Element


```python
fo.element.unique()
```

## Year


```python
fo.year.unique()
```

## Unit

```python
fo.unit.unique()
```

## Flag

```python
fo.flag.unique()
```

```python
fo.columns
```

```python

```
