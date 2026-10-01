import React from 'react';

export function MarkdownText({ content }: { content: string }) {
  const lines = content.split('\n');
  const rendered: React.ReactNode[] = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (isTableRow(line) && isTableDivider(lines[index + 1])) {
      const headers = parseCells(line);
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length && isTableRow(lines[index])) {
        rows.push(parseCells(lines[index]));
        index += 1;
      }
      rendered.push(<table className="response-table" key={`table-${index}`}><thead><tr>{headers.map((cell, cellIndex) => <th key={cellIndex}>{formatInline(cell)}</th>)}</tr></thead><tbody>{rows.map((row, rowIndex) => <tr key={rowIndex}>{headers.map((_, cellIndex) => <td key={cellIndex}>{formatInline(row[cellIndex] || '')}</td>)}</tr>)}</tbody></table>);
      index -= 1;
      continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const Heading = heading[1].length <= 2 ? 'h4' : 'h5';
      rendered.push(<Heading key={index}>{formatInline(heading[2])}</Heading>);
      continue;
    }
    if (/^\s*([-*_])(?:\s*\1){2,}\s*$/.test(line)) { rendered.push(<hr key={index} />); continue; }
    if (line.startsWith('- ') || line.startsWith('•')) { rendered.push(<div className="markdown-bullet" key={index}><span>•</span><span>{formatInline(line.replace(/^[-•]\s*/, ''))}</span></div>); continue; }
    if (/^\d+\.\s+/.test(line)) { rendered.push(<div className="markdown-bullet" key={index}><span>{line.match(/^\d+/)?.[0]}.</span><span>{formatInline(line.replace(/^\d+\.\s+/, ''))}</span></div>); continue; }
    if (!line.trim()) { rendered.push(<div className="markdown-gap" key={index} />); continue; }
    rendered.push(<p key={index}>{formatInline(line.replace(/^>\s?/, ''))}</p>);
  }
  return <div className="markdown-text">{rendered}</div>;
}

function isTableRow(line?: string) { return Boolean(line && line.includes('|')); }
function isTableDivider(line?: string) { return Boolean(line && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line)); }
function parseCells(line: string) { return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim()); }

function formatInline(value: string) {
  const parts = value.split(/(\*\*.*?\*\*|`.*?`|\*[^*\n]+\*|_[^_\n]+_)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1, -1)}</code>;
    if ((part.startsWith('*') && part.endsWith('*')) || (part.startsWith('_') && part.endsWith('_'))) return <em key={index}>{part.slice(1, -1)}</em>;
    return part;
  });
}
