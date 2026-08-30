import { Injectable, signal } from '@angular/core';

export type DialogType = 'success' | 'warning' | 'error';

export interface DialogConfig {
  type: DialogType;
  title: string;
  message: string;
  showCancel?: boolean;
  onConfirm?: () => void;
  onCancel?: () => void;
}

@Injectable({
  providedIn: 'root'
})
export class DialogService {
  public currentDialog = signal<DialogConfig | null>(null);
  public isClosing = signal<boolean>(false);

  open(config: DialogConfig) {
    this.isClosing.set(false);
    this.currentDialog.set(config);
  }

  close() {
    this.isClosing.set(true);
    // 等待動畫結束後清空 (0.3s 動畫時間)
    setTimeout(() => {
      this.currentDialog.set(null);
      this.isClosing.set(false);
    }, 300);
  }

  confirm() {
    const dialog = this.currentDialog();
    if (dialog?.onConfirm) {
      dialog.onConfirm();
    }
    this.close();
  }

  cancel() {
    const dialog = this.currentDialog();
    if (dialog?.onCancel) {
      dialog.onCancel();
    }
    this.close();
  }
}
