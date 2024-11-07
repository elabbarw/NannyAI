import psutil
from difflib import get_close_matches
import re

class ProgramTerminator:
    def __init__(self, logger):
        self.logger = logger
        self.min_similarity = 0.6  # Minimum similarity score for fuzzy matching

    def get_running_processes(self):
        """Get list of all running processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                processes.append({
                    'pid': proc.pid,
                    'name': proc.info['name'],
                    'exe': proc.info['exe']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes

    def normalize_program_name(self, name):
        """Normalize program name for better matching"""
        # Remove file extensions, convert to lowercase, remove special chars
        name = re.sub(r'\.(exe|app|dmg|dll)$', '', name.lower())
        name = re.sub(r'[^a-z0-9]', '', name)
        return name

    def find_matching_process(self, target_name):
        """Find the best matching process using fuzzy matching"""
        if not target_name:
            return None

        normalized_target = self.normalize_program_name(target_name)
        processes = self.get_running_processes()
        
        # Create a list of normalized process names
        process_names = [self.normalize_program_name(p['name']) for p in processes]
        
        # Find closest matches
        matches = get_close_matches(normalized_target, process_names, n=1, cutoff=self.min_similarity)
        
        if matches:
            # Find the original process info for the matched normalized name
            matched_norm_name = matches[0]
            for proc in processes:
                if self.normalize_program_name(proc['name']) == matched_norm_name:
                    self.logger.info(f"Found matching process: {proc['name']} (PID: {proc['pid']}) for target: {target_name}")
                    return proc
        
        return None

    def terminate_program(self, program_name):
        """Terminate a program using fuzzy matching"""
        if not program_name:
            return False

        try:
            # Find matching process
            matching_process = self.find_matching_process(program_name)
            
            if not matching_process:
                self.logger.warning(f"No matching process found for: {program_name}")
                return False

            # Get process by PID
            process = psutil.Process(matching_process['pid'])
            
            # Log before attempting to terminate
            self.logger.info(f"Attempting to terminate: {matching_process['name']} (PID: {matching_process['pid']})")
            
            # Terminate the process
            process.terminate()
            
            # Wait for process to terminate (with timeout)
            try:
                process.wait(timeout=3)
                self.logger.info(f"Successfully terminated: {matching_process['name']}")
                return True
            except psutil.TimeoutExpired:
                # Force kill if regular termination fails
                process.kill()
                self.logger.info(f"Force killed: {matching_process['name']}")
                return True
                
        except psutil.NoSuchProcess:
            self.logger.error(f"Process no longer exists: {program_name}")
            return False
        except psutil.AccessDenied:
            self.logger.error(f"Access denied when trying to terminate: {program_name}")
            return False
        except Exception as e:
            self.logger.error(f"Error terminating program {program_name}: {str(e)}")
            return False

    def safe_to_terminate(self, process_info):
        """Check if it's safe to terminate a process"""
        # List of protected process names
        protected_processes = {
            'system', 'systemd', 'explorer.exe', 'finder', 
            'windows defender', 'antivirus'
        }
        
        if not process_info:
            return False
            
        process_name = process_info['name'].lower()
        
        # Check against protected processes
        for protected in protected_processes:
            if protected in process_name:
                self.logger.warning(f"Attempted to terminate protected process: {process_name}")
                return False
                
        return True