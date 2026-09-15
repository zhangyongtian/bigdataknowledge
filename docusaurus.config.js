/*
 *
 *  Licensed to the Apache Software Foundation (ASF) under one or more
 *  contributor license agreements.  See the NOTICE file distributed with
 *  this work for additional information regarding copyright ownership.
 *  The ASF licenses this file to You under the Apache License, Version 2.0
 *  (the "License"); you may not use this file except in compliance with
 *  the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 */

// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

const math = require('remark-math');
const katex = require('rehype-katex');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: '大数据知识库',
  tagline: '致力于规范大数据数据质量标准、集成、开发、管理、监控以及部署知识库，帮助您快速构建起稳定、高效、可弹性伸缩的大数据平台',
  url: 'https://zhangyongtian.github.io/',
  //这里部署的时候要修改成 baseUrl: '/'
  //这里部署的时候要修改成 baseUrl: '/BigdataKnowledge-website/'
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.13.24/dist/katex.min.css',
      type: 'text/css',
      integrity:
        'sha384-odtC+0UGzzFL/6PNoE8rX/SPcQDXBJ+uRepguP4QkPCm2LBxH3FA3y+fKSiJ+AmM',
      crossorigin: 'anonymous',
    },
  ],

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'BigdataKnowledge', // Usually your GitHub org/user name.
  projectName: 'BigdataKnowledge', // Usually your repo name.

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ["zh-Hans","en"],
    localeConfigs: {
      en: {
        htmlLang: 'en-GB',
      },
      // You can omit a locale (e.g. fr) if you don't need to override the defaults
    },
  },
  themes: [
    [
      require.resolve("@easyops-cn/docusaurus-search-local"),
      /** @type {import("@easyops-cn/docusaurus-search-local").PluginOptions} */
      ({
        // config url is: https://github.com/easyops-cn/docusaurus-search-local#theme-options
        hashed: true,
        indexDocs: true,
        indexPages: true,
        highlightSearchTermsOnTargetPage: false, // Highlight search terms on target page.
        explicitSearchResultPath: true,
        searchBarPosition: "right",
        searchBarShortcutHint: false, // Whether to show keyboard shortcut hint in search bar. Disable it if you need to hide the hint while shortcut is still enabled.
        language: ["zh", "en"],
        hideSearchBarWithNoSearchContext: true,
      }),
    ],
  ],

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          lastVersion: 'current',
          versions: {
            current: {
            label: '最新版本(unreleased)',
            path: '',
            },
          },
          path: "docs",
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/zhangyongtian/bigdataknowledge/tree/dev',
          beforeDefaultRemarkPlugins: [math],
          rehypePlugins: [katex],
        },
        blog: {
          showReadingTime: true,
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          blogSidebarTitle: '全部博文',
          blogSidebarCount: 'ALL',
          editUrl:
            'https://github.com/zhangyongtian/bigdataknowledge/tree/dev',
          beforeDefaultRemarkPlugins: [math],
          rehypePlugins: [katex],
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  // Workaround for Node v24 + webpack5 + Docusaurus 2.4：
  // Docusaurus 2.4 内部会给 webpack.ProgressPlugin 传 { name, color, reporters, reporter }
  // 这些老字段，但 Node v24 里 webpack5 的 schema-utils 不认，直接报 ValidationError。
  // 解决方案：注册一个临时的 Docusaurus 插件，用它的 configureWebpack() 钩子拿到最终
  // webpack config 的引用，遍历 plugins 数组找到 ProgressPlugin 实例，重建一个只含
  // 合法 schema 字段（handler / percentBy / modules / progressBar …）的新实例。
  plugins: [
    function pluginNode24ProgressFix(context, opts) {
      return {
        name: 'node24-progress-plugin-fix',
        configureWebpack(config, isServer, utils) {
          const { ProgressPlugin } = require('webpack');
          if (!Array.isArray(config.plugins)) return {};
          for (let i = 0; i < config.plugins.length; i++) {
            const p = config.plugins[i];
            if (p instanceof ProgressPlugin && p.options) {
              const old = p.options;
              const clean = {};
              for (const k of ['handler', 'percentBy', 'activeModules',
                               'dependencies', 'dependenciesCount', 'entries',
                               'estimatedTime', 'modules', 'modulesCount',
                               'phaseTimings', 'profile', 'progressBar']) {
                if (k in old) clean[k] = old[k];
              }
              const reporters = (Array.isArray(old.reporters) ? old.reporters : [])
                .concat((typeof old.reporter === 'function') ? [old.reporter] : []);
              if (reporters.length) {
                const prev = typeof clean.handler === 'function' ? clean.handler : null;
                clean.handler = (pct, msg, ...args) => {
                  if (prev) prev(pct, msg, ...args);
                  for (const r of reporters) { try { r(pct, msg, ...args); } catch (_) {} }
                };
              }
              config.plugins[i] = new ProgressPlugin(clean);
            }
          }
          return {};
        },
      };
    },
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'light',
        disableSwitch: false,
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: 'BigdataKnowledge',
        logo: {
          alt: 'BigdataKnowledge Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'doc',
            docId: '概览',
            position: 'left',
            label: 'Docs',
            activeBasePath: "docs"
          },
        // {
        //   type: 'docsVersionDropdown',
        //   position: 'right',
        //   dropdownItemsAfter: [{to: '/versions', label: 'All versions'}],
        //   dropdownActiveClassDisabled: true,
        // },
          {to: '/blog', label: 'Blog', position: 'left'},
          {
            href: 'https://github.com/zhangyongtian/bigdataknowledge',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Docs',
                to: '/docs/概览',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              // {
              //   label: 'Stack Overflow',
              //   href: 'https://stackoverflow.com/questions/tagged/athenaserving',
              // },
              {
                label: 'Github Discussion',
                href: 'https://github.com/zhangyongtian/bigdataknowledge',
              },
              // {
              //   label: 'Twitter',
              //   href: 'https://twitter.com/docusaurus',
              // },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'Blog',
                to: '/blog',
              },
              {
                label: 'GitHub Issues',
                href: 'https://github.com/zhangyongtian/bigdataknowledge',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} My Project, Inc. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
