import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DialogService, DialogType } from '../../services/dialog';

@Component({
  selector: 'app-dialog',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dialog.html',
  styleUrl: './dialog.css',
})
export class Dialog {
  dialogService = inject(DialogService);

  getIconClass(type: DialogType): string {
    const icons: Record<DialogType, string> = {
      success: 'fa-solid fa-check text-green-500',
      warning: 'fa-solid fa-exclamation text-yellow-600',
      error: 'fa-solid fa-xmark text-red-500'
    };
    return icons[type] || icons['success'];
  }

  getIconBgClass(type: DialogType): string {
    const bgs: Record<DialogType, string> = {
      success: 'bg-green-100',
      warning: 'bg-yellow-100',
      error: 'bg-red-100'
    };
    return bgs[type] || bgs['success'];
  }

  getConfirmBtnClass(type: DialogType): string {
    const btns: Record<DialogType, string> = {
      success: 'bg-matPrimary hover:bg-matPrimaryHover',
      warning: 'bg-red-500 hover:bg-red-600',
      error: 'bg-matPrimary hover:bg-matPrimaryHover'
    };
    return btns[type] || btns['success'];
  }
}
