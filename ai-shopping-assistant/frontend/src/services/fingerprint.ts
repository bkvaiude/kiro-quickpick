// types/fingerprint.types.ts
export interface FingerprintComponents {
    userAgent: string;
    language: string;
    platform: string;
    screenResolution: string;
    colorDepth: string;
    timezoneOffset: string;
    languages?: string;
    hardwareConcurrency: string;
    deviceMemory?: string;
    canvas?: string;
    webgl?: string;
    plugins?: string;
  }
  
  export interface FingerprintResult {
    fingerprint: string;
    components: FingerprintComponents;
    timestamp: number;
  }
  
  // services/BrowserFingerprintService.ts
  class BrowserFingerprintService {
    private cachedFingerprint: string | null = null;
    private cacheTimestamp: number = 0;
    private readonly CACHE_DURATION = 60 * 60 * 1000; // 5 minutes
  
    /**
     * Simple hash function for consistent string hashing
     * @param str - String to hash
     * @returns Hashed string
     */
    private simpleHash(str: string): string {
      let hash = 0;
      if (str.length === 0) return hash.toString();
      
      for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
      }
      
      return Math.abs(hash).toString(36);
    }
  
    /**
     * Get canvas fingerprint for additional uniqueness
     * @returns Canvas fingerprint hash or null
     */
    private getCanvasFingerprint(): string | null {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        if (!ctx) return null;
        
        // Draw some text and shapes
        ctx.textBaseline = 'alphabetic';
        ctx.fillStyle = '#f60';
        ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = '#069';
        ctx.font = '11pt Arial';
        ctx.fillText('Browser fingerprint', 2, 15);
        ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
        ctx.font = '18pt Arial';
        ctx.fillText('Simple test', 4, 45);
        
        // Get canvas data and hash it
        const canvasData = canvas.toDataURL();
        return this.simpleHash(canvasData);
        
      } catch (error) {
        console.warn('Canvas fingerprinting failed:', error);
        return null;
      }
    }
  
    /**
     * Get WebGL fingerprint for additional uniqueness
     * @returns WebGL fingerprint hash or null
     */
    private getWebGLFingerprint(): string | null {
      try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        if (!gl) return null;
        
        const renderer = gl.getParameter(gl.RENDERER);
        const vendor = gl.getParameter(gl.VENDOR);
        const version = gl.getParameter(gl.VERSION);
        const shadingLanguageVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
        
        const webglInfo = [renderer, vendor, version, shadingLanguageVersion].join('|');
        return this.simpleHash(webglInfo);
        
      } catch (error) {
        console.warn('WebGL fingerprinting failed:', error);
        return null;
      }
    }
  
    /**
     * Collect all fingerprint components
     * @returns Fingerprint components object
     */
    private collectFingerprintComponents(): FingerprintComponents {
      const components: FingerprintComponents = {
        userAgent: navigator.userAgent || 'unknown',
        language: navigator.language || (navigator as any).userLanguage || 'unknown',
        platform: navigator.platform || 'unknown',
        screenResolution: `${screen.width}x${screen.height}`,
        colorDepth: screen.colorDepth?.toString() || 'unknown',
        timezoneOffset: new Date().getTimezoneOffset().toString(),
        hardwareConcurrency: navigator.hardwareConcurrency?.toString() || 'unknown'
      };
  
      // Optional components
      if (navigator.languages) {
        components.languages = navigator.languages.join(',');
      }
  
      if ((navigator as any).deviceMemory) {
        components.deviceMemory = (navigator as any).deviceMemory.toString();
      }
  
      // Canvas fingerprint
      const canvasFingerprint = this.getCanvasFingerprint();
      if (canvasFingerprint) {
        components.canvas = canvasFingerprint;
      }
  
      // WebGL fingerprint
      const webglFingerprint = this.getWebGLFingerprint();
      if (webglFingerprint) {
        components.webgl = webglFingerprint;
      }
  
      // Plugins (if available)
      if (navigator.plugins && navigator.plugins.length > 0) {
        const plugins = Array.from(navigator.plugins)
          .map(plugin => plugin.name)
          .sort()
          .join(',');
        components.plugins = plugins;
      }
  
      return components;
    }
  
    /**
     * Generate browser fingerprint
     * @param useCache - Whether to use cached result (default: true)
     * @returns Fingerprint result with components and hash
     */
    public generateFingerprint(useCache: boolean = true): FingerprintResult {
      const now = Date.now();
  
      // Return cached result if valid and cache is enabled
      if (useCache && this.cachedFingerprint && (now - this.cacheTimestamp) < this.CACHE_DURATION) {
        return {
          fingerprint: this.cachedFingerprint,
          components: this.collectFingerprintComponents(), // Always return fresh components for debugging
          timestamp: this.cacheTimestamp
        };
      }
  
      try {
        // Collect all fingerprint components
        const components = this.collectFingerprintComponents();
        
        // Create fingerprint array from components
        const fingerprintArray: string[] = [
          components.userAgent,
          components.language,
          components.platform,
          components.screenResolution,
          components.colorDepth,
          components.timezoneOffset,
          components.hardwareConcurrency
        ];
  
        // Add optional components if they exist
        if (components.languages) fingerprintArray.push(components.languages);
        if (components.deviceMemory) fingerprintArray.push(components.deviceMemory);
        if (components.canvas) fingerprintArray.push(components.canvas);
        if (components.webgl) fingerprintArray.push(components.webgl);
        if (components.plugins) fingerprintArray.push(components.plugins);
        
        // Join all components and hash
        const fingerprintString = fingerprintArray.join('|');
        const hashedFingerprint = this.simpleHash(fingerprintString);
        
        // Cache the result
        this.cachedFingerprint = hashedFingerprint;
        this.cacheTimestamp = now;
        
        return {
          fingerprint: hashedFingerprint,
          components,
          timestamp: now
        };
        
      } catch (error) {
        console.error('Error generating fingerprint:', error);
        
        // Fallback fingerprint
        const fallbackFingerprint = this.simpleHash(
          navigator.userAgent + screen.width + screen.height
        );
        
        return {
          fingerprint: fallbackFingerprint,
          components: this.collectFingerprintComponents(),
          timestamp: now
        };
      }
    }
  
    /**
     * Get just the fingerprint string (most common use case)
     * @param useCache - Whether to use cached result (default: true)
     * @returns Fingerprint string
     */
    public getFingerprint(useCache: boolean = true): string {
      return this.generateFingerprint(useCache).fingerprint;
    }
  
    /**
     * Clear cached fingerprint (force regeneration on next call)
     */
    public clearCache(): void {
      this.cachedFingerprint = null;
      this.cacheTimestamp = 0;
    }
  
    /**
     * Check if fingerprint is cached and valid
     * @returns True if cached fingerprint is valid
     */
    public isCached(): boolean {
      const now = Date.now();
      return !!(this.cachedFingerprint && (now - this.cacheTimestamp) < this.CACHE_DURATION);
    }
  }
  
  // Create singleton instance
const browserFingerprintService = new BrowserFingerprintService();

// Export singleton instance and class
export { BrowserFingerprintService };
export default browserFingerprintService;