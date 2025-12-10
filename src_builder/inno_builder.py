"""
Inno Setup Builder
使用 Inno Setup 创建 Windows 安装器
"""
import subprocess
import sys
from pathlib import Path
from typing import Optional


class InnoSetupBuilder:
    """Inno Setup 构建器"""
    
    def __init__(self):
        self.inno_compiler = self._find_inno_compiler()
    
    def _find_inno_compiler(self) -> Optional[Path]:
        """查找 Inno Setup 编译器"""
        possible_paths = [
            Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
            Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def is_available(self) -> bool:
        """检查 Inno Setup 是否可用"""
        return self.inno_compiler is not None
    
    def build(self, script_path: Path, output_dir: Optional[Path] = None) -> bool:
        """
        使用 Inno Setup 编译安装脚本
        
        Args:
            script_path: .iss 脚本文件路径
            output_dir: 输出目录（可选，默认使用脚本中定义的）
        
        Returns:
            bool: 是否成功
        """
        if not self.is_available():
            print("❌ ERROR: Inno Setup compiler not found!")
            print("   Please install Inno Setup 6 from: https://jrsoftware.org/isdl.php")
            return False
        
        if not script_path.exists():
            print(f"❌ ERROR: Script not found: {script_path}")
            return False
        
        print(f"📝 Inno Setup script: {script_path.absolute()}")
        print(f"🔧 Compiler: {self.inno_compiler}")
        
        # 构建命令
        cmd = [str(self.inno_compiler), str(script_path.absolute())]
        
        if output_dir:
            cmd.extend([f"/O{output_dir.absolute()}"])
        
        print(f"📝 Command: {' '.join(cmd)}")
        print("\n▶️  Starting Inno Setup compilation...")
        print("")
        
        # 执行编译
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 显示输出
            if result.stdout:
                print(result.stdout)
            
            if result.returncode != 0:
                print(f"\n❌ ERROR: Compilation failed with exit code {result.returncode}")
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
                return False
            
            print("\n✅ Inno Setup compilation successful!")
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Failed to run Inno Setup compiler: {e}")
            return False
    
    def get_output_filename(self, script_path: Path) -> Optional[str]:
        """
        从脚本中解析输出文件名
        
        Args:
            script_path: .iss 脚本路径
        
        Returns:
            输出文件名，如果无法解析则返回 None
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('OutputBaseFilename='):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass
        
        return None
