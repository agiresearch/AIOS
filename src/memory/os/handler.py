from src.memory.os.persistent import PersistentMemory
from src.memory.os.virtual import VirtualMemory

class MemoryHandler:
    def __init__(self, execute, virtual_allocation=0.6, max_allocation=8000):
        self.core = execute

        self.persistent = PersistentMemory()
        self.virtual = VirtualMemory(max_buffer=virtual_allocation*max_allocation)

        self.persistent.initialize()

    def chain(self, message):
        self.virtual.add_memory(role='user', content=message)

        while not self.virtual._check_buffer():
            res1, res2 = self.virtual.clip_memory()

            if res1:
                self.persistent.stack(role=res1.role, phrase=res1.content)
            if res2:
                self.persistent.stack(role=res2.role, phrase=res2.content)

        #when persistent memory is still undeveloped, adding it in dilutes results
        try:
            prompt = f"""
                You are an AI Agent who responds in turn. You are provided with the recent parts of the current conversation, as well as \
                relevant chunks of previous information.
            
                Previous Information: \n{self.persistent.recall(format=True)}

                Current Conversation: \n{self.virtual.read_memory()}
            """
        except:
            prompt = f"""
                You are an AI Agent who responds in turn. You are provided with the recent parts of the current conversation.
            
                Current Conversation: \n{self.virtual.read_memory()}
            """


        response = self.core(prompt)

        self.virtual.add_memory(role='assistant', content=response)

        return response

        

# p = PersistentMemory()
# p.initialize()
# p.stack(role='user', phrase='cow likes sheep')
# p.stack(role='user', phrase='cow likes sheep')
# p.stack(role='user', phrase='cow likes sheep')
# k = p.recall(queries=['cows'], format=True)
# print(k)

# test_closed_llm()