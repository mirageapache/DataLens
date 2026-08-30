import { Directive, ElementRef, HostListener, Input, Renderer2, inject } from '@angular/core';

@Directive({
  selector: '[appTooltip]',
  standalone: true
})
export class TooltipDirective {
  @Input('appTooltip') tooltipText = '';
  @Input() tooltipPosition: 'top' | 'bottom' | 'left' | 'right' = 'top';

  private tooltipElement: HTMLElement | null = null;
  private el = inject(ElementRef);
  private renderer = inject(Renderer2);

  @HostListener('mouseenter') onMouseEnter() {
    if (!this.tooltipText) return;

    this.tooltipElement = this.renderer.createElement('div');
    const text = this.renderer.createText(this.tooltipText);
    
    // 根據 prototype 設定樣式
    if (this.tooltipElement) {
      this.tooltipElement.className = `absolute bg-gray-800 text-white text-sm px-3 py-2 rounded shadow-lg z-50 animate-fade-in w-max max-w-xs tooltip-arrow-${this.tooltipPosition}`;
      this.renderer.appendChild(this.tooltipElement, text);
      this.renderer.appendChild(document.body, this.tooltipElement);
      this.setPosition();
    }
  }

  @HostListener('mouseleave') onMouseLeave() {
    this.removeTooltip();
  }
  
  @HostListener('window:scroll') onScroll() {
    this.removeTooltip();
  }

  private setPosition() {
    if (!this.tooltipElement) return;

    const hostPos = this.el.nativeElement.getBoundingClientRect();
    const tooltipPos = this.tooltipElement.getBoundingClientRect();

    let top = 0;
    let left = 0;

    switch (this.tooltipPosition) {
      case 'top':
        top = hostPos.top - tooltipPos.height - 8;
        left = hostPos.left + (hostPos.width - tooltipPos.width) / 2;
        break;
      case 'bottom':
        top = hostPos.bottom + 8;
        left = hostPos.left + (hostPos.width - tooltipPos.width) / 2;
        break;
      case 'left':
        top = hostPos.top + (hostPos.height - tooltipPos.height) / 2;
        left = hostPos.left - tooltipPos.width - 8;
        break;
      case 'right':
        top = hostPos.top + (hostPos.height - tooltipPos.height) / 2;
        left = hostPos.right + 8;
        break;
    }

    this.renderer.setStyle(this.tooltipElement, 'top', `${top + window.scrollY}px`);
    this.renderer.setStyle(this.tooltipElement, 'left', `${left + window.scrollX}px`);
  }

  private removeTooltip() {
    if (this.tooltipElement) {
      this.renderer.removeChild(document.body, this.tooltipElement);
      this.tooltipElement = null;
    }
  }
}
