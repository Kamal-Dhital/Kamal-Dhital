#!/usr/bin/env python3
"""
GitHub Profile Stats Generator
Generates beautiful, dynamic README with comprehensive GitHub statistics
"""

import os
import requests
import json
from datetime import datetime, timezone
from collections import defaultdict, Counter
import time

class GitHubStatsGenerator:
    def __init__(self):
        self.token = os.environ.get('GITHUB_TOKEN')
        self.username = os.environ.get('GITHUB_USERNAME')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        })
    
    def make_request(self, url, params=None):
        """Make GitHub API request with rate limit handling"""
        try:
            response = self.session.get(url, params=params)
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait_time = max(reset_time - int(time.time()), 60)
                print(f"Rate limit hit, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                response = self.session.get(url, params=params)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def get_user_info(self):
        """Get user profile information"""
        url = f'https://api.github.com/users/{self.username}'
        return self.make_request(url)
    
    def get_repositories(self):
        """Get all user repositories"""
        repos = []
        page = 1
        while True:
            url = f'https://api.github.com/users/{self.username}/repos'
            params = {
                'type': 'owner',
                'sort': 'updated',
                'per_page': 100,
                'page': page
            }
            
            data = self.make_request(url, params)
            if not data:
                break
            
            repos.extend(data)
            if len(data) < 100:
                break
            page += 1
        
        return repos
    
    def get_language_stats(self, repos):
        """Get detailed language statistics"""
        languages = defaultdict(int)
        language_repos = defaultdict(set)
        
        for repo in repos[:30]:  # Limit to avoid rate limits
            if repo['fork']:
                continue
                
            url = f"https://api.github.com/repos/{self.username}/{repo['name']}/languages"
            lang_data = self.make_request(url)
            
            if lang_data:
                for lang, bytes_count in lang_data.items():
                    languages[lang] += bytes_count
                    language_repos[lang].add(repo['name'])
        
        return dict(languages), {k: list(v) for k, v in language_repos.items()}
    
    def get_contribution_stats(self):
        """Get contribution statistics for current year"""
        # This would require GraphQL API for detailed contribution data
        # For now, we'll use repository activity as a proxy
        current_year = datetime.now().year
        contributions = 0
        
        # Estimate based on recent commits (simplified)
        url = f'https://api.github.com/users/{self.username}/events'
        events = self.make_request(url)
        
        if events:
            current_year_events = [
                e for e in events 
                if datetime.fromisoformat(e['created_at'].replace('Z', '+00:00')).year == current_year
            ]
            contributions = len(current_year_events)
        
        return contributions
    
    def calculate_advanced_stats(self, user, repos):
        """Calculate advanced statistics"""
        stats = {
            'total_repos': len(repos),
            'public_repos': len([r for r in repos if not r['private']]),
            'total_stars': sum(r['stargazers_count'] for r in repos),
            'total_forks': sum(r['forks_count'] for r in repos),
            'total_watchers': sum(r['watchers_count'] for r in repos),
            'total_size': sum(r['size'] for r in repos),  # in KB
            'followers': user['followers'],
            'following': user['following'],
        }
        
        # Repository type analysis
        original_repos = [r for r in repos if not r['fork']]
        forked_repos = [r for r in repos if r['fork']]
        
        stats.update({
            'original_repos': len(original_repos),
            'forked_repos': len(forked_repos),
            'avg_stars_per_repo': stats['total_stars'] / max(len(original_repos), 1),
            'most_starred_repo': max(repos, key=lambda x: x['stargazers_count'])['name'] if repos else 'None',
            'most_starred_stars': max(repos, key=lambda x: x['stargazers_count'])['stargazers_count'] if repos else 0,
        })
        
        return stats
    
    def generate_modern_readme(self, user, stats, languages, lang_repos):
        """Generate a modern, beautiful README"""
        
        # Calculate language percentages
        total_bytes = sum(languages.values())
        lang_percentages = {
            lang: (bytes_count / total_bytes * 100) 
            for lang, bytes_count in languages.items()
        } if total_bytes > 0 else {}
        
        top_languages = sorted(lang_percentages.items(), key=lambda x: x[1], reverse=True)[:8]
        
        # Language color mapping
        lang_colors = {
            'Python': '#3776ab', 'JavaScript': '#f1e05a', 'TypeScript': '#2b7489',
            'Java': '#b07219', 'C++': '#f34b7d', 'C': '#555555', 'C#': '#239120',
            'Go': '#00ADD8', 'Rust': '#dea584', 'PHP': '#4F5D95', 'Ruby': '#701516',
            'Swift': '#ffac45', 'Kotlin': '#F18E33', 'Dart': '#00B4AB', 'R': '#276DC3',
            'Scala': '#c22d40', 'Shell': '#89e051', 'HTML': '#e34c26', 'CSS': '#1572B6',
            'Vue': '#4FC08D', 'React': '#61DAFB', 'Angular': '#DD0031'
        }
        
        current_time = datetime.now(timezone.utc)
        
        readme_content = f"""
<div align="center">
  
# 👋 Hello, I'm {user['name'] or user['login']}!

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=00D4AA&center=true&vCenter=true&width=600&lines=Welcome+to+my+GitHub+profile!;{user['public_repos']}%2B+repositories+and+counting...;{stats['total_stars']}+stars+earned+so+far!;Always+learning%2C+always+coding!" alt="Typing SVG" />

</div>

{f'> *{user["bio"]}*' if user.get('bio') else ''}

---

## 🎯 Quick Overview

<div align="center">
  
<table>
<tr>
<td align="center">
  <img src="https://github-readme-stats.vercel.app/api?username={self.username}&show_icons=true&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=00D4AA&text_color=FFFFFF&icon_color=00D4AA" alt="GitHub Stats" />
</td>
<td align="center">
  <img src="https://github-readme-streak-stats.herokuapp.com/?user={self.username}&theme=tokyonight&hide_border=true&background=0D1117&stroke=00D4AA&ring=00D4AA&fire=FF6B6B&currStreakLabel=00D4AA" alt="GitHub Streak" />
</td>
</tr>
</table>

</div>

---

## 📊 Detailed Statistics

<div align="center">

| 📈 **Metric** | 🔢 **Value** | 📈 **Metric** | 🔢 **Value** |
|:---:|:---:|:---:|:---:|
| **🏗️ Total Repositories** | `{stats['total_repos']}` | **⭐ Total Stars** | `{stats['total_stars']:,}` |
| **📚 Original Repos** | `{stats['original_repos']}` | **🍴 Total Forks** | `{stats['total_forks']:,}` |
| **🔄 Forked Repos** | `{stats['forked_repos']}` | **👥 Followers** | `{stats['followers']:,}` |
| **📦 Repository Size** | `{stats['total_size'] / 1024:.1f} MB` | **🏆 Most Starred** | `{stats['most_starred_repo']} ({stats['most_starred_stars']} ⭐)` |

</div>

---

## 🛠️ Technology Stack & Languages

<div align="center">

<img src="https://github-readme-stats.vercel.app/api/top-langs/?username={self.username}&layout=donut-vertical&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=00D4AA&text_color=FFFFFF&langs_count=8" alt="Top Languages" />

</div>

### 💻 Tech Stack Icons

<div align="center">

{self._generate_tech_stack_icons(languages)}

</div>

### 📊 Language Usage Breakdown

<div align="center">

{self._generate_language_bars(top_languages, lang_colors)}

</div>

### 🔧 Development Tools & Frameworks

<div align="center">

{self._generate_tools_frameworks()}

</div>

---

## 🏆 GitHub Achievements

<div align="center">

<img src="https://github-profile-trophy.vercel.app/?username={self.username}&theme=tokyonight&no-frame=true&no-bg=true&margin-w=4&column=7" alt="GitHub Trophies" />

</div>

---

## 📈 Contribution Activity

<div align="center">

<img src="https://github-readme-activity-graph.vercel.app/graph?username={self.username}&bg_color=0D1117&color=00D4AA&line=00D4AA&point=FFFFFF&area=true&hide_border=true" alt="Contribution Graph" />

</div>

---

## 🎨 Profile Highlights

<div align="center">

### 💻 Most Used Languages in Projects
{self._generate_language_project_info(lang_repos, top_languages[:5])}

### 📅 Account Information
- 🗓️ **Joined GitHub:** {datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')).strftime('%B %Y')}
- 📍 **Location:** {user['location'] or 'Earth 🌍'}
- 🌐 **Website:** {f"[{user['blog']}]({user['blog']})" if user.get('blog') else 'Not specified'}
- ✉️ **Public Email:** {user['email'] or 'Not public'}

</div>

---

## 🤝 Let's Connect!

<div align="center">

{self._generate_social_links(user)}

[![Profile Views](https://komarev.com/ghpvc/?username={self.username}&color=00D4AA&style=for-the-badge&label=PROFILE+VIEWS)](https://github.com/{self.username})

</div>

---

<div align="center">

### 🔄 Auto-Updated Every Hour

**Last Updated:** `{current_time.strftime('%A, %B %d, %Y at %H:%M UTC')}`

<sub>This README is automatically generated and updated using GitHub Actions 🤖</sub>

---

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer&text=Thanks%20for%20visiting!&fontSize=24&fontColor=fff&animation=twinkling" />

</div>
"""
        
        return readme_content.strip()
    
    def _generate_tech_stack_icons(self, languages):
        """Generate technology stack icons based on used languages"""
        
        # Language to icon mapping
        tech_icons = {
            'Python': 'https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white',
            'JavaScript': 'https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black',
            'TypeScript': 'https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white',
            'Java': 'https://img.shields.io/badge/Java-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white',
            'C++': 'https://img.shields.io/badge/C%2B%2B-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white',
            'C': 'https://img.shields.io/badge/C-00599C?style=for-the-badge&logo=c&logoColor=white',
            'C#': 'https://img.shields.io/badge/C%23-239120?style=for-the-badge&logo=c-sharp&logoColor=white',
            'Go': 'https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white',
            'Rust': 'https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white',
            'PHP': 'https://img.shields.io/badge/PHP-777BB4?style=for-the-badge&logo=php&logoColor=white',
            'Ruby': 'https://img.shields.io/badge/Ruby-CC342D?style=for-the-badge&logo=ruby&logoColor=white',
            'Swift': 'https://img.shields.io/badge/Swift-FA7343?style=for-the-badge&logo=swift&logoColor=white',
            'Kotlin': 'https://img.shields.io/badge/Kotlin-0095D5?style=for-the-badge&logo=kotlin&logoColor=white',
            'Dart': 'https://img.shields.io/badge/Dart-0175C2?style=for-the-badge&logo=dart&logoColor=white',
            'R': 'https://img.shields.io/badge/R-276DC3?style=for-the-badge&logo=r&logoColor=white',
            'Scala': 'https://img.shields.io/badge/Scala-DC322F?style=for-the-badge&logo=scala&logoColor=white',
            'Shell': 'https://img.shields.io/badge/Shell_Script-121011?style=for-the-badge&logo=gnu-bash&logoColor=white',
            'HTML': 'https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white',
            'CSS': 'https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white',
            'Vue': 'https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vue.js&logoColor=4FC08D',
            'React': 'https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB',
            'Angular': 'https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white',
            'SCSS': 'https://img.shields.io/badge/SASS-hotpink.svg?style=for-the-badge&logo=SASS&logoColor=white',
            'Less': 'https://img.shields.io/badge/less-2B4C80?style=for-the-badge&logo=less&logoColor=white',
            'Jupyter Notebook': 'https://img.shields.io/badge/jupyter-%23FA0F00.svg?style=for-the-badge&logo=jupyter&logoColor=white'
        }
        
        # Get icons for languages the user actually uses
        used_icons = []
        for lang in languages.keys():
            if lang in tech_icons:
                used_icons.append(f"![{lang}]({tech_icons[lang]})")
        
        # If no matching languages, show common tech stack
        if not used_icons:
            common_icons = [
                "![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)",
                "![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)",
                "![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)",
                "![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)"
            ]
            return ' '.join(common_icons)
        
        # Arrange icons in rows of 6
        rows = [used_icons[i:i+6] for i in range(0, len(used_icons), 6)]
        return '\n\n'.join(' '.join(row) for row in rows)
    
    def _generate_tools_frameworks(self):
        """Generate development tools and frameworks section"""
        
        tools_frameworks = [
            # Version Control & CI/CD
            "![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)",
            "![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)",
            "![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)",
            
            # IDEs & Editors
            "![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)",
            "![PyCharm](https://img.shields.io/badge/pycharm-143?style=for-the-badge&logo=pycharm&logoColor=black&color=black&labelColor=green)",
            "![Vim](https://img.shields.io/badge/VIM-%2311AB00.svg?style=for-the-badge&logo=vim&logoColor=white)",
            
            # Databases
            "![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white)",
            "![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)",
            "![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)",
            "![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)",
            
            # Cloud & Hosting
            "![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)",
            "![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)",
            "![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white)",
            "![Vercel](https://img.shields.io/badge/vercel-%23000000.svg?style=for-the-badge&logo=vercel&logoColor=white)",
            "![Netlify](https://img.shields.io/badge/netlify-%23000000.svg?style=for-the-badge&logo=netlify&logoColor=#00C7B7)",
            
            # Frameworks & Libraries
            "![Node.js](https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white)",
            "![Express.js](https://img.shields.io/badge/express.js-%23404d59.svg?style=for-the-badge&logo=express&logoColor=%2361DAFB)",
            "![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)",
            "![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)",
            "![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)",
            
            # DevOps & Tools
            "![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)",
            "![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white)",
            "![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)",
            "![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)",
            
            # Design & UI
            "![Figma](https://img.shields.io/badge/figma-%23F24E1E.svg?style=for-the-badge&logo=figma&logoColor=white)",
            "![Adobe Photoshop](https://img.shields.io/badge/adobe%20photoshop-%2331A8FF.svg?style=for-the-badge&logo=adobe%20photoshop&logoColor=white)",
            "![Canva](https://img.shields.io/badge/Canva-%2300C4CC.svg?style=for-the-badge&logo=Canva&logoColor=white)"
        ]
        
        # Organize into categories
        sections = {
            "**Version Control & CI/CD**": tools_frameworks[0:3],
            "**IDEs & Development Environment**": tools_frameworks[3:6],
            "**Databases**": tools_frameworks[6:10],
            "**Cloud Platforms & Hosting**": tools_frameworks[10:15],
            "**Frameworks & Backend**": tools_frameworks[15:20],
            "**DevOps & System Tools**": tools_frameworks[20:24],
            "**Design & Creative Tools**": tools_frameworks[24:27]
        }
        
        result = []
        for category, badges in sections.items():
            result.append(f"{category}")
            result.append(' '.join(badges))
            result.append("")  # Empty line for spacing
        
        return '\n'.join(result)
    
    def _generate_language_project_info(self, lang_repos, top_languages):
        """Generate language project information"""
        info = []
        for lang, percentage in top_languages:
            repos = lang_repos.get(lang, [])
            repo_count = len(repos)
            if repo_count > 0:
                repo_list = ', '.join(repos[:3])
                if repo_count > 3:
                    repo_list += f" and {repo_count - 3} more"
                info.append(f"**{lang}** ({percentage:.1f}%) - Used in {repo_count} repositories: {repo_list}")

        return '\n'.join(info) if info else "Language data being processed..."
    
        """Generate visual language usage bars"""
        bars = []
        for lang, percentage in top_languages:
            color = lang_colors.get(lang, '#666666')
            bar_length = max(int(percentage / 2), 1)  # Scale down for display
            bar = '█' * bar_length + '░' * max(50 - bar_length, 0)
            bars.append(f"**{lang}** `{percentage:.1f}%` \n{bar}")
        
        return '\n\n'.join(bars) if bars else "No language data available"
    
    def _generate_tech_stack_icons(self, languages):
        """Generate technology stack icons based on used languages"""
        
        # Language to icon mapping with modern badges
        tech_icons = {
            'Python': 'https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white',
            'JavaScript': 'https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black',
            'TypeScript': 'https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white',
            'Java': 'https://img.shields.io/badge/Java-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white',
            'C++': 'https://img.shields.io/badge/C%2B%2B-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white',
            'C': 'https://img.shields.io/badge/C-00599C?style=for-the-badge&logo=c&logoColor=white',
            'C#': 'https://img.shields.io/badge/C%23-239120?style=for-the-badge&logo=c-sharp&logoColor=white',
            'Go': 'https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white',
            'Rust': 'https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white',
            'PHP': 'https://img.shields.io/badge/PHP-777BB4?style=for-the-badge&logo=php&logoColor=white',
            'Ruby': 'https://img.shields.io/badge/Ruby-CC342D?style=for-the-badge&logo=ruby&logoColor=white',
            'Swift': 'https://img.shields.io/badge/Swift-FA7343?style=for-the-badge&logo=swift&logoColor=white',
            'Kotlin': 'https://img.shields.io/badge/Kotlin-0095D5?style=for-the-badge&logo=kotlin&logoColor=white',
            'Dart': 'https://img.shields.io/badge/Dart-0175C2?style=for-the-badge&logo=dart&logoColor=white',
            'R': 'https://img.shields.io/badge/R-276DC3?style=for-the-badge&logo=r&logoColor=white',
            'Scala': 'https://img.shields.io/badge/Scala-DC322F?style=for-the-badge&logo=scala&logoColor=white',
            'Shell': 'https://img.shields.io/badge/Shell_Script-121011?style=for-the-badge&logo=gnu-bash&logoColor=white',
            'HTML': 'https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white',
            'CSS': 'https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white',
            'Vue': 'https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vue.js&logoColor=4FC08D',
            'Jupyter Notebook': 'https://img.shields.io/badge/jupyter-%23FA0F00.svg?style=for-the-badge&logo=jupyter&logoColor=white',
            'SCSS': 'https://img.shields.io/badge/SASS-hotpink.svg?style=for-the-badge&logo=SASS&logoColor=white'
        }
        
        # Get icons for languages the user actually uses
        used_icons = []
        for lang in languages.keys():
            if lang in tech_icons:
                used_icons.append(f"![{lang}]({tech_icons[lang]})")
        
        # If no matching languages, show common tech stack
        if not used_icons:
            common_icons = [
                "![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)",
                "![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)",
                "![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)",
                "![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)",
                "![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)"
            ]
            return ' '.join(common_icons)
        
        # Arrange icons in rows of 6 for better display
        rows = [used_icons[i:i+6] for i in range(0, len(used_icons), 6)]
        return '\n\n'.join(' '.join(row) for row in rows)
    
    def _generate_language_bars(self, top_languages, lang_colors):
        """Generate visual language usage bars"""
        if not top_languages:
            return "📊 Language data is being analyzed..."
        
        bars = []
        for lang, percentage in top_languages:
            color = lang_colors.get(lang, '#666666')
            # Create visual progress bar
            filled_blocks = int(percentage / 2)  # Scale to max 50 blocks
            empty_blocks = max(25 - filled_blocks, 0)  # Total bar length of 25
            
            progress_bar = '█' * filled_blocks + '▒' * empty_blocks
            bars.append(f"**{lang}** `{percentage:.1f}%`\n`{progress_bar}`")
        
        return '\n\n'.join(bars)
    
    def _generate_tools_frameworks(self):
        """Generate comprehensive development tools and frameworks section"""
        
        tools_categories = {
            "**🔧 Development Tools**": [
                "![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)",
                "![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)",
                "![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)",
                "![PyCharm](https://img.shields.io/badge/pycharm-143?style=for-the-badge&logo=pycharm&logoColor=black&color=black&labelColor=green)",
                "![Vim](https://img.shields.io/badge/VIM-%2311AB00.svg?style=for-the-badge&logo=vim&logoColor=white)",
                "![Postman](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white)"
            ],
            
            "**🌐 Frontend Frameworks**": [
                "![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)",
                "![Vue.js](https://img.shields.io/badge/vuejs-%2335495e.svg?style=for-the-badge&logo=vuedotjs&logoColor=%234FC08D)",
                "![Angular](https://img.shields.io/badge/angular-%23DD0031.svg?style=for-the-badge&logo=angular&logoColor=white)",
                "![Next JS](https://img.shields.io/badge/Next-black?style=for-the-badge&logo=next.js&logoColor=white)",
                "![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)",
                "![Bootstrap](https://img.shields.io/badge/bootstrap-%23563D7C.svg?style=for-the-badge&logo=bootstrap&logoColor=white)"
            ],
            
            "**⚙️ Backend & APIs**": [
                "![NodeJS](https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white)",
                "![Express.js](https://img.shields.io/badge/express.js-%23404d59.svg?style=for-the-badge&logo=express&logoColor=%2361DAFB)",
                "![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)",
                "![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)",
                "![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)",
                "![GraphQL](https://img.shields.io/badge/-GraphQL-E10098?style=for-the-badge&logo=graphql&logoColor=white)"
            ],
            
            "**🗄️ Databases**": [
                "![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)",
                "![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)",
                "![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white)",
                "![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)",
                "![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)"
            ],
            
            "**☁️ Cloud & DevOps**": [
                "![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)",
                "![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)",
                "![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)",
                "![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white)",
                "![Vercel](https://img.shields.io/badge/vercel-%23000000.svg?style=for-the-badge&logo=vercel&logoColor=white)",
                "![Netlify](https://img.shields.io/badge/netlify-%23000000.svg?style=for-the-badge&logo=netlify&logoColor=#00C7B7)"
            ],
            
            "**🤖 AI/ML & Data Science**": [
                "![TensorFlow](https://img.shields.io/badge/TensorFlow-%23FF6F00.svg?style=for-the-badge&logo=TensorFlow&logoColor=white)",
                "![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=for-the-badge&logo=PyTorch&logoColor=white)",
                "![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)",
                "![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)",
                "![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)"
            ]
        }
        
        result = []
        for category, badges in tools_categories.items():
            result.append(f"\n{category}\n")
            # Split badges into rows of 6 for better layout
            rows = [badges[i:i+6] for i in range(0, len(badges), 6)]
            for row in rows:
                result.append(' '.join(row))
            result.append("")  # Empty line for spacing
        
        return '\n'.join(result)
    
        """Generate language project information"""
        info = []
        for lang, percentage in top_languages:
            repos = lang_repos.get(lang, [])
            repo_count = len(repos)
            if repo_count > 0:
                repo_list = ', '.join(repos[:3])
                if repo_count > 3:
                    repo_list += f" and {repo_count - 3} more"
                info.append(f"**{lang}** ({percentage:.1f}%) - Used in {repo_count} repositories: {repo_list}")
        
        return '\n'.join(info) if info else "Language data being processed..."
    
    def _generate_social_links(self, user):
        """Generate social media links"""
        links = []
        
        if user.get('blog'):
            links.append(f"[![Website](<https://img.shields.io/badge/Website-00D4AA?style=for-the-badge&logo=google-chrome&logoColor=white>)]({user['blog']})")
        
        if user.get('twitter_username'):
            links.append(f"[![Twitter](https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/{user['twitter_username']})")
        
        if user.get('email'):
            links.append(f"[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:{user['email']})")
        
        links.append(f"[![GitHub](https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/{self.username})")
        
        return ' '.join(links)
    
    def run(self):
        """Main execution function"""
        print("🚀 Starting GitHub Profile Stats Generation...")
        
        # Get user information
        print("📊 Fetching user information...")
        user = self.get_user_info()
        if not user:
            print("❌ Failed to fetch user information")
            return False
        
        # Get repositories
        print("📚 Fetching repositories...")
        repos = self.get_repositories()
        if not repos:
            print("❌ Failed to fetch repositories")
            return False
        
        print(f"✅ Found {len(repos)} repositories")
        
        # Get language statistics
        print("🔍 Analyzing language usage...")
        languages, lang_repos = self.get_language_stats(repos)
        
        # Calculate advanced statistics
        print("📈 Calculating advanced statistics...")
        stats = self.calculate_advanced_stats(user, repos)
        
        # Generate README
        print("📝 Generating README content...")
        readme_content = self.generate_modern_readme(user, stats, languages, lang_repos)
        
        # Write to file
        print("💾 Writing README.md...")
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print("✅ Profile README generated successfully!")
        print(f"📊 Stats Summary:")
        print(f"   - {stats['total_repos']} repositories")
        print(f"   - {stats['total_stars']} total stars")
        print(f"   - {len(languages)} programming languages")
        
        return True

if __name__ == "__main__":
    generator = GitHubStatsGenerator()
    success = generator.run()
    
    if not success:
        exit(1)
