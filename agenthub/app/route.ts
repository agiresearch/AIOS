import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export async function GET() {
  const htmlPath = path.join(process.cwd(), 'public', 'pages', 'index.html');
//   const cssPath = path.join(process.cwd(), 'public', 'custom.css');
//   const jsPath = path.join(process.cwd(), 'public', 'custom.js');

//   const [html, css, js] = await Promise.all([
//     fs.readFile(htmlPath, 'utf8'),
//     fs.readFile(cssPath, 'utf8'),
//     fs.readFile(jsPath, 'utf8'),
//   ]);

    const html = await fs.readFile(htmlPath, 'utf8');

//   const fullHtml = html
//     .replace('</head>', `<style>${css}</style></head>`)
//     .replace('</body>', `<script>${js}</script></body>`);

  return new NextResponse(html, {
    headers: { 'Content-Type': 'text/html' },
  });
}