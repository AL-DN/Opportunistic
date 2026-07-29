## Opportunisic

The goal of this project is to build not only a `private, efficent way of organizing and storing a SWE contributions across their entire career` but also making the data store quickly searchable. I hope to build an agent ontop of this that can customize sections of resume (work experience, personal projects, open source contribtions) to the job posting. While simulaneously scanning the internet that best fit the SWE.

### Call Stack

1. Git push hook for git commits ~ then we know the commits are official and not rewinded (etc)
2. prompt llm:
    You are a helpful assisant tasked to extract important values from this code including,
    a project_id (parent folder name), libraries, data structures and algorithms utilized. Along with big O space and time complexity along with a result 
    string that explains How did it improve the current or if new what did this result in. + `git commit code`

3. Turn LLM 
4. Summary Output
{
    project_id str
    libraries list[str]
    data_structusres[str] ** Could use basemodels with descriptions later to help summaries **
    algorithms[str]
    bigo_time_complexity str
    bigo_space complexity str
    result str " 
}
5. Save to Json
