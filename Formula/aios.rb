class Aios < Formula
    desc "FastAPI server application"
    homepage ""
    head do
      url ".", :using => :git, :branch => "v.20"  # Specify your current branch
      version "1.0.0"
    end
    
    # Only add Python dependency if system Python is not available
    depends_on "python@3.10" => :optional
    
    def install
      libexec.install Dir["*.py"]
      libexec.install Dir["requirements.txt"] if File.exist?("requirements.txt")
      
      # Check for system Python 3.10
      if system "which python3.10 >/dev/null 2>&1"
        system_python = `which python3.10`.strip
        system system_python, "-m", "pip", "install", "--prefix=#{libexec}", "fastapi", "uvicorn"
        
        # Create wrapper script that uses system Python
        (bin/"aios").write <<~EOS
          #!/bin/bash
          export PYTHONPATH="#{libexec}/lib/python3.10/site-packages:$PYTHONPATH"
          if [ "$1" = "run" ]; then
            pid_file="#{var}/aios.pid"
            if [ -f "$pid_file" ]; then
              echo "AIOS is already running"
              exit 1
            fi
            
            cd #{libexec}
            nohup #{system_python} -m uvicorn server1:app --host 0.0.0.0 --port 8000 > #{var}/aios.log 2>&1 &
            echo $! > "$pid_file"
            echo "AIOS started on port 8000"
          
          elif [ "$1" = "stop" ]; then
            pid_file="#{var}/aios.pid"
            if [ ! -f "$pid_file" ]; then
              echo "AIOS is not running"
              exit 1
            fi
            
            pid=$(cat "$pid_file")
            kill $pid
            rm "$pid_file"
            echo "AIOS stopped"
          
          else
            echo "Usage: aios [run|stop]"
            exit 1
          fi
        EOS
      else
        # Only use Homebrew Python if system Python 3.10 is not available
        ohai "System Python 3.10 not found, using Homebrew Python"
        
        include Language::Python::Virtualenv
        venv = virtualenv_create(libexec, Formula["python@3.10"].opt_bin/"python3.10")
        if File.exist?("requirements.txt")
          venv.pip_install_and_link buildpath/"requirements.txt"
        else
          venv.pip_install "fastapi"
          venv.pip_install "uvicorn"
        end
        
        (bin/"aios").write <<~EOS
          #!/bin/bash
          if [ "$1" = "run" ]; then
            pid_file="#{var}/aios.pid"
            if [ -f "$pid_file" ]; then
              echo "AIOS is already running"
              exit 1
            fi
            
            cd #{libexec}
            nohup #{libexec}/bin/uvicorn server1:app --host 0.0.0.0 --port 8000 > #{var}/aios.log 2>&1 &
            echo $! > "$pid_file"
            echo "AIOS started on port 8000"
          
          elif [ "$1" = "stop" ]; then
            pid_file="#{var}/aios.pid"
            if [ ! -f "$pid_file" ]; then
              echo "AIOS is not running"
              exit 1
            fi
            
            pid=$(cat "$pid_file")
            kill $pid
            rm "$pid_file"
            echo "AIOS stopped"
          
          else
            echo "Usage: aios [run|stop]"
            exit 1
          fi
        EOS
      end
      
      chmod 0755, bin/"aios"
    end
  
    def post_install
      (var/"aios").mkpath
    end
  
    test do
      system "#{bin}/aios", "--help"
    end
  end