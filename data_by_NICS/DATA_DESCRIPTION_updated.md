# **Xiaoxiao Taiwan Channel Comment Data Description**

**Download Date**: 2025-09-30 **Channel**: 曉曉看台灣 / Xiaoxiao Taiwan ([https://www.youtube.com/@曉曉看台灣](https://www.youtube.com/@%E6%9B%89%E6%9B%89%E7%9C%8B%E5%8F%B0%E7%81%A3)) **Tool**: yt-dlp

***


## **📊 Data Statistics**

- **Total Videos**: 21

- **Total Comments**: 1,292

  - **Root Comments**: 965 (74.69%)

  - **Reply Comments**: 327 (25.31%)

- **Data Format**: JSON (.info.json)

***


## **🔧 Download Command**

    yt-dlp --skip-download --write-comments \
      --extractor-args "youtube:comment_sort=top" \
      --extractor-args "youtube:max_comments=all,all,all,all" \
      -o "data/youtube_analysis/xiaoxiao_taiwan/%(id)s_%(title)s" \
      "https://www.youtube.com/@曉曉看台灣/videos"


### **Command Explanation:**

- `--skip-download`: Skip video file download, only download metadata

- `--write-comments`: Download comments to info.json file

- `--extractor-args "youtube:comment_sort=top"`: Sort comments by "Top" (most liked)

- `--extractor-args "youtube:max_comments=all,all,all,all"`: Download all comments and replies

  - Format: `max-comments,max-parents,max-replies,max-replies-per-thread`

- `-o "%(id)s_%(title)s"`: Output filename format as "VideoID\_Title"

***


## **📁 File Structure**

Each video corresponds to one `.info.json` file:

    VIDEO_ID_VideoTitle.info.json

Example:

    bLlEKrXxILs_韓國記者公然羞辱台湾棒球！结果被朴赞浩当场打脸.info.json

***


## **📋 Data Structure**

### **1. Video Metadata**

Each `.info.json` file contains the following video information:

|                 |          |                                  |                              |
| --------------- | -------- | -------------------------------- | ---------------------------- |
| **Field**       | **Type** | **Description**                  | **Example**                  |
| `id`            | string   | Video ID                         | `"bLlEKrXxILs"`              |
| `title`         | string   | Video title                      | `"韓國記者公然羞辱台湾棒球..."`          |
| `channel`       | string   | Channel name                     | `"曉曉看台灣"`                    |
| `channel_id`    | string   | Channel ID                       | `"UC-Zl2LRUSEXQRsM1RD3eI1Q"` |
| `upload_date`   | string   | Upload date (YYYYMMDD)           | `"20250710"`                 |
| `view_count`    | integer  | View count                       | `147099`                     |
| `like_count`    | integer  | Like count                       | `1855`                       |
| `comment_count` | integer  | Comment count (YouTube reported) | `149`                        |
| `duration`      | integer  | Video duration (seconds)         | `1061`                       |
| `description`   | string   | Video description                |                              |
| `comments`      | array    | Comments array (see below)       |                              |


### **2. Comment Data Structure**

Each comment contains the following fields:

|                      |          |                                                                       |                                  |
| -------------------- | -------- | --------------------------------------------------------------------- | -------------------------------- |
| **Field**            | **Type** | **Description**                                                       | **Example**                      |
| `id`                 | string   | Unique comment ID                                                     | `"Ugyk4eix1_nNnzPQdBd4AaABAg"`   |
| `text`               | string   | Comment content                                                       | `"靠，韓國算啥！王建民兩年19勝..."`           |
| `author`             | string   | Author username                                                       | `"@佐藤龍也-d1e"`                    |
| `author_id`          | string   | Author channel ID                                                     | `"UCsEjFGJe2ftNF0rgWHnveIA"`     |
| `author_url`         | string   | Author channel URL                                                    | `"https://www.youtube.com/@..."` |
| `author_thumbnail`   | string   | Author avatar URL                                                     | `"https://yt3.ggpht.com/..."`    |
| `author_is_uploader` | boolean  | Whether author is video uploader                                      | `false`                          |
| `author_is_verified` | boolean  | Whether author is verified                                            | `false`                          |
| `parent`             | string   | Parent comment ID (`"root"` = top-level comment, otherwise parent ID) | `"root"`                         |
| `timestamp`          | integer  | Unix timestamp (seconds)                                              | `1759201200`                     |
| `_time_text`         | string   | Relative time text                                                    | `"3 hours ago"`                  |
| `like_count`         | integer  | Like count                                                            | `0`                              |
| `is_favorited`       | boolean  | Whether marked as favorite                                            | `false`                          |
| `is_pinned`          | boolean  | Whether pinned                                                        | `false`                          |


### **3. Reply Data Structure (Flat Storage)**

**Important**: yt-dlp stores replies in a **flat structure**, not nested. All comments (both root and replies) are in the same `comments` array.

**How to identify replies:**

- **Root comment**: `"parent": "root"`

- **Reply comment**: `"parent": "<parent_comment_id>"`

**Example from** `bLlEKrXxILs_韓國記者公然羞辱台湾棒球！...info.json`**:**

    // Root comment (parent = "root")
    {
      "id": "Ugx5ry2UXS4IBCS2umV4AaABAg",
      "text": "這種ai 影片還有人信哦？訪問沒講的，自己造謠瞎掰出來的，還都不用負責 相關韓妹tv 韓國留學生 都用同一種模式騙點閱",
      "author": "@廖偉智-y1s",
      "parent": "root",
      ...
    }

    // Reply to the above comment (parent = parent comment ID)
    {
      "id": "Ugx5ry2UXS4IBCS2umV4AaABAg.ALiciEd0LZVAMtnhb6xwWk",
      "text": "沒錯就是討好台灣騙點閱  根本沒這回事",
      "author": "@shine1106-vn",
      "parent": "Ugx5ry2UXS4IBCS2umV4AaABAg",
      ...
    }

**To verify this yourself:**

1. Open file: `bLlEKrXxILs_韓國記者公然羞辱台湾棒球！结果被朴赞浩当场打脸。王建民被骂运气好，台湾被讽只看啦啦队，朴赞浩火力全开反击，爆气护王建民！一句话让全台网友热泪盈眶.info.json`

2. Search for comment ID: `Ugx5ry2UXS4IBCS2umV4AaABAg.ALiciEd0LZVAMtnhb6xwWk`

3. Verify its `parent` field is `Ugx5ry2UXS4IBCS2umV4AaABAg` (the root comment ID)

4. Notice the reply ID contains the parent ID as a prefix

***


## **⏰ Timestamp Format**

### **timestamp field**

- **Type**: `integer`

- **Format**: Unix timestamp (seconds)

- **Description**: Seconds since 1970-01-01 00:00:00 UTC

- **Example**: `1759201200` = `2025-09-30 11:00:00 UTC`


### **Python Conversion Example:**

    from datetime import datetime

    timestamp = 1759201200
    dt = datetime.fromtimestamp(timestamp)
    print(dt.strftime('%Y-%m-%d %H:%M:%S'))  # 2025-09-30 11:00:00


### **\_time\_text field**

- **Type**: `string`

- **Format**: Relative time (e.g., "3 hours ago", "2 days ago")

- **Description**: Relative time text displayed by YouTube

- **Note**: This is relative time, **not suitable** for precise time analysis

***


## **⚠️ Important Findings and Limitations**

### **1. Reply Data Structure**

**Finding**: The dataset contains **327 reply comments (25.31%)** among 1,292 total comments.

**Storage Format**: Replies are stored in a **flat structure** (not nested):

- All comments (root + replies) are in the same `comments` array

- Use the `parent` field to identify reply relationships:

  - `"parent": "root"` → Root/top-level comment

  - `"parent": "<comment_id>"` → Reply to that comment

**Parameter Configuration**:

    # Download all comments and all replies (used for this dataset)
    --extractor-args "youtube:max_comments=all,all,all,all"

    # Download max 1000 replies, max 10 per thread
    --extractor-args "youtube:max_comments=all,all,1000,10"

**Format**: `max-comments,max-parents,max-replies,max-replies-per-thread`


### **2. Time Precision**

- ✅ **timestamp**: Unix timestamp (second-level precision), suitable for timeline analysis

- ❌ **\_time\_text**: Relative time text, not suitable for precise analysis


### **3. Sorting Method**

This download used `comment_sort=top` (most popular), therefore:

- Prioritizes downloading comments with the highest like counts

- May miss newer comments with lower like counts

**Alternative Options**:

    # Sort by time (newest first)
    --extractor-args "youtube:comment_sort=new"

***


## **📊 Comment Distribution**

### **Top 10 Videos (by comment count):**

|          |              |                                                                                                  |
| -------- | ------------ | ------------------------------------------------------------------------------------------------ |
| **Rank** | **Comments** | **Video Title**                                                                                  |
| 1        | 814          | Chinese streamer films Taiwan's filth and danger at night, livestream shocks foreign netizens... |
| 2        | 195          | Japanese website lists 14 characteristics of Taiwanese people...                                 |
| 3        | 149          | Korean reporter openly humiliates Taiwan baseball! Gets shut down by Park Chan-ho...             |
| 4        | 45           | Yaya is denounced across the web, mainland streamers collectively expel Yaya...                  |
| 5        | 17           | Korean woman compares Taiwan and mainland China...                                               |
| 6        | 16           | American TV show compares global security and civic quality...                                   |
| 7        | 12           | Why does Europe only recognize Taiwan's flag...                                                  |
| 8        | 11           | Famous Chinese patriotic influencer Sima Nan investigated for tax evasion...                     |
| 9        | 6            | Mainland spouse Yaya (Liu Zhenya), Enqi, Xiaowei's miserable situation...                        |
| 10       | 6            | Mainland spouse "Yaya in Taiwan" real identity exposed by netizens...                            |

***


## **🔍 Data Usage Recommendations**

### **Suitable Scenarios**

✅ **Suitable for**:

- Comment content analysis (Simplified/Traditional Chinese detection)

- Author account analysis (account ID, channel)

- Timeline analysis (using `timestamp`)

- Like count analysis

- Duplicate comment detection

- **Reply network analysis** (using `parent` field to build comment threads)

- **Comment thread analysis** (reconstruct conversations from flat structure)

- Engagement pattern analysis (reply rates, response times)

❌ **Not suitable for**:

- Relative time analysis (`_time_text` is imprecise)


### **Python Example: Building Comment Threads**

    import json

    # Load data
    with open('bLlEKrXxILs_韓國記者公然羞辱台湾棒球！...info.json', 'r') as f:
        data = json.load(f)

    # Organize comments by parent
    threads = {}
    for comment in data['comments']:
        parent = comment['parent']
        if parent not in threads:
            threads[parent] = []
        threads[parent].append(comment)

    # Get all root comments
    root_comments = threads.get('root', [])
    print(f"Root comments: {len(root_comments)}")

    # Get replies for a specific comment
    comment_id = "Ugx5ry2UXS4IBCS2umV4AaABAg"
    replies = threads.get(comment_id, [])
    print(f"Replies to {comment_id}: {len(replies)}")

***


## **📚 Related Documentation**

- [YouTube Data Collection Complete Review](about:blank)

- [yt-dlp Official Documentation](https://github.com/yt-dlp/yt-dlp)

- [yt-dlp Manual](https://man.archlinux.org/man/extra/yt-dlp/yt-dlp.1.en)

***


## **🔗 Data Citation**

If using this data, please cite:

    Xiaoxiao Taiwan Channel Comment Dataset
    Download Date: 2025-09-30
    Tool: yt-dlp
    Channel: https://www.youtube.com/@曉曉看台灣

***
