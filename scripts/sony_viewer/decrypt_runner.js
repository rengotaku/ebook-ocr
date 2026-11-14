#!/usr/bin/env node
// Sony ビューアの復号ワーカーを読み込み、ページごとにヘッダと画像を復号する。
//
// 使い方: node decrypt_runner.js <worker.js> <jobs.jsonl> <outdir>
//   jobs.jsonl の 1 行は {"id": "123", "header": "h.bin", "image": "i.bin"}
//   出力は <outdir>/<id>.webp.bin（並べ替え前の WebP）と <outdir>/<id>.order.bin
//
// ワーカー本体はビューアが配信する JavaScript をそのまま使う（リポジトリには含めない）。
// 鍵はワーカーの末尾に書かれていて HAR ごとに違うので、ソースから取り出す。
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const IV = [0, 1, 2, 3];

function extractKey(source, workerPath) {
  const match = source.match(/var n=\[0,1,2,3\],e=\[([0-9,]+)\]/);
  if (!match) {
    throw new Error(`${workerPath} から復号鍵を取り出せなかった（ビューアの実装が変わった可能性）`);
  }
  return match[1].split(',').map(Number);
}

function loadWorker(workerPath) {
  let source = fs.readFileSync(workerPath, 'utf8');
  const key = extractKey(source, workerPath);
  // 内部の復号関数を取り出せるように差し替える
  source = source.replace('self.postMessage("load"),e=void 0',
                          'self.postMessage("load"),self.__decrypt=n,e=void 0');
  const sandbox = {
    self: { addEventListener: () => {}, postMessage: () => {} },
    console, Uint8Array, Uint32Array, Int32Array, DataView, ArrayBuffer, Math, Date,
  };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: workerPath });
  if (typeof sandbox.self.__decrypt !== 'function') {
    throw new Error('復号ワーカーから関数を取り出せなかった（ビューアの実装が変わった可能性）');
  }
  return { decrypt: sandbox.self.__decrypt, key };
}

const toArrayBuffer = (buffer) => buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
const wordsAt = (buffer, offset) =>
  Array.from(new Uint32Array(Uint8Array.from(buffer.slice(offset, offset + 16)).buffer));

function main() {
  const [workerPath, jobsPath, outDir] = process.argv.slice(2);
  if (!workerPath || !jobsPath || !outDir) {
    console.error('usage: node decrypt_runner.js <worker.js> <jobs.jsonl> <outdir>');
    process.exit(2);
  }
  const { decrypt, key } = loadWorker(workerPath);
  const jobs = fs.readFileSync(jobsPath, 'utf8').split('\n').filter((line) => line.trim())
    .map((line) => JSON.parse(line));

  for (const job of jobs) {
    try {
      // ヘッダは [uint32 サイズ][20 バイト MAC][暗号文]
      const page = fs.readFileSync(job.header);
      const body = page.slice(4 + 20, page.length);
      const decryptedHeader = Buffer.from(decrypt(key, IV, toArrayBuffer(body)));
      const pageKey = wordsAt(decryptedHeader, 4);
      const order = decryptedHeader.slice(20);

      const encryptedImage = fs.readFileSync(job.image);
      const image = Buffer.from(decrypt(pageKey, IV, toArrayBuffer(encryptedImage)));

      fs.writeFileSync(path.join(outDir, `${job.id}.webp.bin`), image);
      fs.writeFileSync(path.join(outDir, `${job.id}.order.bin`), order);
      console.log(JSON.stringify({ id: job.id, ok: image.slice(0, 4).toString('latin1') === 'RIFF' }));
    } catch (error) {
      console.log(JSON.stringify({ id: job.id, error: String((error && error.message) || error) }));
    }
  }
}

main();
