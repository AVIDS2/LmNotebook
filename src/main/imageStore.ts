/**
 * 图片分离存储服务
 * 大于阈值的图片存储到文件系统，小图片保持 Base64 内嵌
 */
import { join } from 'path'
import { existsSync, mkdirSync, writeFileSync, readFileSync, unlinkSync, readdirSync } from 'fs'
import { createHash } from 'crypto'
import { getConfig } from './database'

// 图片大小阈值：100KB 以上的图片分离存储
const SIZE_THRESHOLD = 100 * 1024

// 自定义协议前缀
export const IMAGE_PROTOCOL = 'origin-image://'

/**
 * 获取图片存储目录
 */
function getImagesDir(): string {
    const config = getConfig()
    const imagesDir = join(config.dataDirectory, 'images')
    if (!existsSync(imagesDir)) {
        mkdirSync(imagesDir, { recursive: true })
    }
    return imagesDir
}

/**
 * 从 Base64 数据计算哈希作为文件名
 */
function hashBase64(base64: string): string {
    return createHash('md5').update(base64).digest('hex')
}

/**
 * 从 Base64 字符串提取 MIME 类型和数据
 */
function parseBase64(dataUrl: string): { mimeType: string; data: string; extension: string } | null {
    const match = dataUrl.match(/^data:(image\/(\w+));base64,(.+)$/)
    if (!match) return null
    
    return {
        mimeType: match[1],
        extension: match[2] === 'jpeg' ? 'jpg' : match[2],
        data: match[3]
    }
}

/**
 * 计算 Base64 数据的实际大小（字节）
 */
function getBase64Size(base64Data: string): number {
    // Base64 编码后大小约为原始大小的 4/3
    // 去掉 data:image/xxx;base64, 前缀后计算
    const base64Only = base64Data.replace(/^data:image\/\w+;base64,/, '')
    return Math.ceil(base64Only.length * 3 / 4)
}

/**
 * 存储图片
 * @param base64DataUrl - 完整的 data:image/xxx;base64,... 字符串
 * @returns 如果图片较大返回 origin-image://xxx.png，否则返回原始 base64
 */
export function storeImage(base64DataUrl: string): string {
    // 检查大小
    const size = getBase64Size(base64DataUrl)
    
    // 小于阈值，保持 Base64
    if (size < SIZE_THRESHOLD) {
        return base64DataUrl
    }
    
    // 解析 Base64
    const parsed = parseBase64(base64DataUrl)
    if (!parsed) {
        console.error('Invalid base64 image data')
        return base64DataUrl
    }
    
    // 生成文件名
    const hash = hashBase64(parsed.data)
    const filename = `${hash}.${parsed.extension}`
    const filepath = join(getImagesDir(), filename)
    
    // 如果文件已存在（相同图片），直接返回引用
    if (existsSync(filepath)) {
        return `${IMAGE_PROTOCOL}${filename}`
    }
    
    // 写入文件
    try {
        const buffer = Buffer.from(parsed.data, 'base64')
        writeFileSync(filepath, buffer)
        console.log(`Image stored: ${filename} (${(size / 1024).toFixed(1)} KB)`)
        return `${IMAGE_PROTOCOL}${filename}`
    } catch (e) {
        console.error('Failed to store image:', e)
        return base64DataUrl
    }
}

/**
 * 读取图片
 * @param imageRef - origin-image://xxx.png 格式的引用
 * @returns Base64 data URL
 */
export function loadImage(imageRef: string): string | null {
    if (!imageRef.startsWith(IMAGE_PROTOCOL)) {
        return null
    }
    
    const filename = imageRef.replace(IMAGE_PROTOCOL, '')
    const filepath = join(getImagesDir(), filename)
    
    if (!existsSync(filepath)) {
        console.error('Image not found:', filepath)
        return null
    }
    
    try {
        const buffer = readFileSync(filepath)
        const extension = filename.split('.').pop() || 'png'
        const mimeType = extension === 'jpg' ? 'image/jpeg' : `image/${extension}`
        return `data:${mimeType};base64,${buffer.toString('base64')}`
    } catch (e) {
        console.error('Failed to load image:', e)
        return null
    }
}

/**
 * 删除图片
 */
export function deleteImage(imageRef: string): boolean {
    if (!imageRef.startsWith(IMAGE_PROTOCOL)) {
        return false
    }
    
    const filename = imageRef.replace(IMAGE_PROTOCOL, '')
    const filepath = join(getImagesDir(), filename)
    
    if (!existsSync(filepath)) {
        return false
    }
    
    try {
        unlinkSync(filepath)
        console.log(`Image deleted: ${filename}`)
        return true
    } catch (e) {
        console.error('Failed to delete image:', e)
        return false
    }
}

/**
 * 获取图片存储统计
 */
export function getImageStats(): { count: number; totalSize: number } {
    const imagesDir = getImagesDir()
    
    try {
        const files = readdirSync(imagesDir).filter(f => 
            /\.(png|jpg|jpeg|gif|webp|svg)$/i.test(f)
        )
        
        let totalSize = 0
        for (const file of files) {
            try {
                const { size } = require('fs').statSync(join(imagesDir, file))
                totalSize += size
            } catch {
                // ignore
            }
        }
        
        return { count: files.length, totalSize }
    } catch {
        return { count: 0, totalSize: 0 }
    }
}

/**
 * 清理未引用的图片（需要传入所有笔记内容中引用的图片列表）
 */
export function cleanupUnusedImages(usedImageRefs: string[]): number {
    const imagesDir = getImagesDir()
    const usedFilenames = new Set(
        usedImageRefs
            .filter(ref => ref.startsWith(IMAGE_PROTOCOL))
            .map(ref => ref.replace(IMAGE_PROTOCOL, ''))
    )
    
    let deletedCount = 0
    
    try {
        const files = readdirSync(imagesDir).filter(f => 
            /\.(png|jpg|jpeg|gif|webp|svg)$/i.test(f)
        )
        
        for (const file of files) {
            if (!usedFilenames.has(file)) {
                try {
                    unlinkSync(join(imagesDir, file))
                    deletedCount++
                    console.log(`Cleaned up unused image: ${file}`)
                } catch {
                    // ignore
                }
            }
        }
    } catch {
        // ignore
    }
    
    return deletedCount
}
