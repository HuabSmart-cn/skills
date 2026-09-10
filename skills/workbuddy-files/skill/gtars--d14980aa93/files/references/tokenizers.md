# Genomic Tokenizers

Tokenizers convert genomic regions into discrete tokens for machine learning applications, particularly useful for training genomic deep learning models.

## Python API

### Creating a Tokenizer

Load tokenizer configurations from various sources:

***REDACTED***
import gtars

# From BED file
tokenizer = ***REDACTED***

# From configuration file
tokenizer = ***REDACTED***

# From region string
tokenizer = ***REDACTED***
```

### Tokenizing Genomic Regions

Convert genomic coordinates to tokens:

***REDACTED***
# Tokenize a single region
token = ***REDACTED***

# Tokenize multiple regions
tokens = ***REDACTED***
for chrom, start, end in regions:
    token = ***REDACTED***
    tokens.append(token)
```

### Token Properties

Access token information:

***REDACTED***
# Get token ID
token_id = ***REDACTED***

# Get genomic coordinates
chrom = token.chromosome
start = token.start
end = token.end

# Get token metadata
metadata = token.metadata
```

## Use Cases

### Machine Learning Preprocessing

Tokenizers are essential for preparing genomic data for ML models:

***REDACTED***
2. **Position encoding**: Create consistent positional encodings across datasets
3. **Data augmentation**: Generate alternative tokenizations for training

### Integration with geniml

The tokenizers module integrates seamlessly with the geniml library for genomic ML:

***REDACTED***
# Tokenize regions for geniml
from gtars.tokenizers import TreeTokenizer
import geniml

tokenizer = ***REDACTED***
tokens = ***REDACTED***

# Use tokens in geniml models
model = geniml.Model(vocab_size=tokenizer.vocab_size)
```

## Configuration Format

Tokenizer configuration files support YAML format:

***REDACTED***
# tokenizer_config.yaml
type: tree
resolution: 1000  # Token resolution in base pairs
chromosomes:
  - chr1
  - chr2
  - chr3
options:
  overlap_handling: merge
  gap_threshold: 100
```

## Performance Considerations

- TreeTokenizer uses efficient data structures for fast tokenization
- Batch tokenization is recommended for large datasets
- Pre-loading tokenizers reduces overhead for repeated operations
